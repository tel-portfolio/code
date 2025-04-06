import logging
import pymysql
from datetime import datetime
from decimal import Decimal
import pandas as pd
import os

# Custom Modules
from utils import create_connection
from data_fetching import fetch_data_from_cache
from signals import (
    calculate_anchored_vwap,
    find_b_signal,
    find_s_signal,
    find_two_bar_b_signal,
    find_two_bar_s_signal
)
from zones import iterate_spy_zones

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database credentials from environment
ALGO_DB_CONFIG = {
    'host': os.getenv('ALGO_DB_HOST'),
    'user': os.getenv('ALGO_DB_USER'),
    'password': os.getenv('ALGO_DB_PASSWORD'),
    'database': 'algo_data'
}

CACHE_DB_CONFIG = {
    'host': os.getenv('ALGO_DB_HOST'),
    'user': os.getenv('ALGO_DB_USER'),
    'password': os.getenv('ALGO_DB_PASSWORD'),
    'database': 'cache'
}


# Utilities
def validate_date_format(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        logging.error(f"Invalid date format: {date_str}. Expected 'YYYY-MM-DD'.")
        return False

def safe_decimal_conversion(value):
    try:
        if value is None:
            logging.warning("Value is None, cannot convert to Decimal.")
            return None
        return Decimal(str(value))
    except (Decimal.InvalidOperation, ValueError) as e:
        logging.error(f"Error converting value to Decimal: {e} | Value: {value}")
        return None


# Database Fetching & Updating
def fetch_all_stocks(algo_connection, limit=None):
    try:
        with algo_connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = "SELECT symbol FROM stocks ORDER BY symbol ASC"
            if limit is not None:
                query += f" LIMIT {limit}"

            logging.info(f"Executing SQL Query: {query}")
            cursor.execute(query)
            result = cursor.fetchall()
            stock_list = [row['symbol'] for row in result] if result else []
            logging.info(f"Fetched {len(stock_list)} stock(s).")
            return stock_list
    except pymysql.MySQLError as e:
        logging.error(f"Error fetching stocks: {e}")
        return []

def update_all_time_high_info(algo_connection, symbol, new_high, new_high_date):
    """
    Unconditionally update the all_time_high and all_time_high_date for a given symbol.
    """
    try:
        logging.debug(
            f"Updating all-time high for {symbol} to {new_high} on {new_high_date.date()}."
        )
        with algo_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE stocks SET all_time_high = %s, all_time_high_date = %s WHERE symbol = %s",
                (float(new_high), new_high_date.strftime('%Y-%m-%d'), symbol)
            )
            algo_connection.commit()
            logging.info(
                f"Updated {symbol} all_time_high to {new_high} on {new_high_date.date()}."
            )
        return new_high, new_high_date
    except pymysql.MySQLError as e:
        logging.error(f"Error updating all-time high info for {symbol}: {e}")
        return None, None

def update_trade_signal(algo_connection, symbol, signal):
    """
    Update the trade_signal field in the stocks table for the given symbol.
    """
    try:
        with algo_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE stocks SET trade_signal = %s WHERE symbol = %s",
                (signal, symbol)
            )
            algo_connection.commit()
            logging.info(f"Updated trade_signal for {symbol} to '{signal}'.")
    except pymysql.MySQLError as e:
        logging.error(f"Error updating trade_signal for {symbol}: {e}")

def update_last_trade_signal(algo_connection, symbol, trade_signal):
    """
    Update the last_trade_signal field in the stocks table for the given symbol.
    """
    try:
        with algo_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE stocks SET last_trade_signal = %s WHERE symbol = %s",
                (trade_signal, symbol)
            )
            algo_connection.commit()
            logging.info(f"Updated last_trade_signal for {symbol} to '{trade_signal}'.")
    except pymysql.MySQLError as e:
        logging.error(f"Error updating last_trade_signal for {symbol}: {e}")

def update_anchored_vwap_at_buy(algo_connection, symbol, anchored_vwap):
    """
    Update the anchored_vwap_at_buy field in the stocks table for the given symbol.
    """
    try:
        with algo_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE stocks SET anchored_vwap_at_buy = %s WHERE symbol = %s",
                (anchored_vwap, symbol)
            )
            algo_connection.commit()
            logging.info(
                f"Updated anchored_vwap_at_buy for {symbol} to {anchored_vwap}."
            )
    except pymysql.MySQLError as e:
        logging.error(f"Error updating anchored_vwap_at_buy for {symbol}: {e}")


# Loading and Using Zone States In-Memory
def load_all_zones(algo_connection):
    """
    Fetch all zone changes, sorted by state_change_date ascending.
    Returns a list of dicts, e.g.:
        [
            {'state_color': 'red', 'state_change_date': datetime(2019,11,21)},
            ...
        ]
    """
    try:
        with algo_connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT state_color, state_change_date
                FROM zone_state
                ORDER BY state_change_date ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            # Convert to datetime objects if needed
            for row in rows:
                row['state_change_date'] = pd.to_datetime(row['state_change_date'])
            return rows
    except pymysql.MySQLError as e:
        logging.error(f"Error loading zone states: {e}")
        return []

def find_zone_for_date(zones_list, target_date):
    """
    Given a sorted list of zones by ascending state_change_date,
    return the zone color that applies to target_date.
    
    We assume zone changes are in effect until the next zone change date.
    So we look for the "latest" zone whose state_change_date <= target_date.
    If none found, default to 'red' (or your desired fallback).
    """
    if not zones_list:
        return 'red'
    
    last_color = None
    for row in zones_list:
        if row['state_change_date'] <= target_date:
            last_color = row['state_color']
        else:
            break
    return last_color if last_color else 'red'


# Signal Processing for a Single Stock/Single Date
def process_stock_data(
    algo_connection,
    symbol,
    current_date,
    market_zone,
    is_today=False,
    daily_data=None
):
    """
    Process a single stock for a single date, using a pre-fetched daily_data DataFrame.
    If today's split_factor != 1.0, we set all_time_high_date to this date, set all_time_high
    to today's close, set last_trade_signal to 'BUY', then STOP further processing for that day.
    Otherwise, proceed with the standard anchored VWAP and signal logic.
    """
    try:
        logging.info(f"Processing {symbol} on {current_date} [Zone: {market_zone}]")

        if daily_data is None or daily_data.empty:
            logging.warning(f"No data available for {symbol} up to {current_date}. Skipping.")
            return

        data = daily_data.copy()

        if not isinstance(data.index, pd.DatetimeIndex):
            logging.error(f"Data for {symbol} must have a DatetimeIndex.")
            return

        if 'close' not in data.columns:
            logging.error(f"Data for {symbol} must contain a 'close' column.")
            return

        MIN_DATA_POINTS = 4
        if len(data) < MIN_DATA_POINTS:
            logging.warning(
                f"Not enough data points for {symbol}. Needed {MIN_DATA_POINTS}, found {len(data)}. Skipping."
            )
            return

        current_date_ts = pd.to_datetime(current_date).normalize()

        split_factor_today = 1.0
        if 'split_factor' in data.columns and current_date_ts in data.index:
            split_factor_today = data.at[current_date_ts, 'split_factor']

        if split_factor_today != 1.0:
            new_close = safe_decimal_conversion(data.at[current_date_ts, 'close'])
            if new_close is not None:
                updated_high, updated_date = update_all_time_high_info(
                    algo_connection=algo_connection,
                    symbol=symbol,
                    new_high=new_close,
                    new_high_date=current_date_ts
                )
                update_last_trade_signal(algo_connection, symbol, 'BUY')
                logging.info(
                    f"[SPLIT DETECTED] {symbol} factor={split_factor_today} on {current_date_ts.date()}. "
                    f"Set all_time_high={new_close}, last_trade_signal=BUY. Skipping other signals this day."
                )
            return 

        with algo_connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT all_time_high, all_time_high_date, last_trade_signal FROM stocks WHERE symbol = %s",
                (symbol,)
            )
            result = cursor.fetchone()

        if result and result['all_time_high'] is not None and result['all_time_high_date'] is not None:
            current_all_time_high = safe_decimal_conversion(result['all_time_high'])
            current_all_time_high_date = pd.to_datetime(result['all_time_high_date'])
            last_trade_signal = result.get('last_trade_signal', None)
            logging.info(
                f"Current all-time high for {symbol}: {current_all_time_high}, "
                f"date: {current_all_time_high_date}, last_signal: {last_trade_signal}"
            )
        else:
            current_all_time_high = safe_decimal_conversion(data.iloc[0]['close'])
            current_all_time_high_date = data.index[0]
            last_trade_signal = None
            updated_high, updated_date = update_all_time_high_info(
                algo_connection,
                symbol,
                current_all_time_high,
                current_all_time_high_date
            )
            if updated_high is None:
                logging.warning(f"Failed to set initial all-time high for {symbol}. Skipping.")
                return
            current_all_time_high, current_all_time_high_date = updated_high, updated_date

        vwap_data = calculate_anchored_vwap(data, anchor_date=current_all_time_high_date, symbol=symbol)
        if vwap_data.empty:
            logging.warning(f"VWAP calculation for {symbol} returned empty data. Skipping.")
            return

        if is_today:
            last_four = vwap_data.tail(4)
            if last_trade_signal == 'BUY':
                # Check for two-bar SELL
                s_date = find_two_bar_s_signal(last_four, symbol)
                if s_date:
                    update_trade_signal(algo_connection, symbol, 'SELL')
                    update_last_trade_signal(algo_connection, symbol, 'SELL')
                    logging.info(f"Two-bar SELL signal for {symbol} on {s_date.date()}.")
                else:
                    update_trade_signal(algo_connection, symbol, None)
            else:
                # Two-bar BUY
                b_date = find_two_bar_b_signal(last_four, symbol)
                if b_date:
                    update_trade_signal(algo_connection, symbol, 'BUY')
                    update_last_trade_signal(algo_connection, symbol, 'BUY')
                    logging.info(f"Two-bar BUY signal for {symbol} on {b_date.date()}.")
                else:
                    update_trade_signal(algo_connection, symbol, None)
        else:
            # Historical signals
            b_signal_detected = False

            # BUY if last_trade_signal != 'BUY'
            if last_trade_signal != 'BUY':
                b_signal_date = find_b_signal(
                    df=vwap_data, symbol=symbol, current_date=current_date_ts
                )
                if b_signal_date:
                    b_signal_date = pd.to_datetime(b_signal_date)
                    if b_signal_date.date() == current_date_ts.date():
                        b_signal_detected = True
                        update_last_trade_signal(algo_connection, symbol, 'BUY')

            # SELL if last_trade_signal == 'BUY'
            if last_trade_signal == 'BUY':
                s_signal_date = find_s_signal(
                    df=vwap_data, symbol=symbol, current_date=current_date_ts
                )
                if s_signal_date:
                    s_signal_date = pd.to_datetime(s_signal_date)
                    if s_signal_date.date() == current_date_ts.date():
                        update_last_trade_signal(algo_connection, symbol, 'SELL')

            if b_signal_detected:
                if b_signal_date in data.index:
                    new_high = safe_decimal_conversion(data.loc[b_signal_date, 'close'])
                    if new_high:
                        updated_high, updated_date = update_all_time_high_info(
                            algo_connection, symbol, new_high, b_signal_date
                        )
                        if updated_high:
                            current_all_time_high = updated_high
                            current_all_time_high_date = updated_date
                            vwap_data = calculate_anchored_vwap(data, anchor_date=current_all_time_high_date, symbol=symbol)

            if last_trade_signal == 'BUY':
                new_data = data[data.index > current_all_time_high_date]
                if not new_data.empty:
                    latest_new_high = new_data['close'].max()
                    latest_new_high_date = new_data['close'].idxmax()
                    if latest_new_high > current_all_time_high:
                        update_all_time_high_info(
                            algo_connection, symbol, latest_new_high, latest_new_high_date
                        )

        logging.info(f"Processed signals for {symbol} on {current_date}.")

    except Exception as e:
        logging.error(f"Error processing {symbol} on {current_date}: {e}")
        

# Summarizing Trade Signals
def fetch_buy_sell_signals(algo_connection):
    """
    Fetch all buy and sell signals from the stocks table.
    """
    try:
        with algo_connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT symbol FROM stocks WHERE trade_signal = 'BUY'")
            buy_signals = [row['symbol'] for row in cursor.fetchall()]
            logging.info(f"Total BUY signals: {len(buy_signals)}")

            cursor.execute("SELECT symbol FROM stocks WHERE trade_signal = 'SELL'")
            sell_signals = [row['symbol'] for row in cursor.fetchall()]
            logging.info(f"Total SELL signals: {len(sell_signals)}")

            return buy_signals, sell_signals
    except pymysql.MySQLError as e:
        logging.error(f"Error fetching buy/sell signals: {e}")
        return [], []

def print_trade_signals(buy_signals, sell_signals, latest_zone_color):
    """
    Print the lists of buy and sell signals, then print the most recent market zone
    before ending.
    """
    logging.info("----- Trade Signals -----")
    if buy_signals:
        logging.info(f"Potential Green Arrow Signals ({len(buy_signals)}):")
        for symbol in buy_signals:
            logging.info(f" - {symbol}")
    else:
        logging.info("No Buy Signals.")

    if sell_signals:
        logging.info(f"Potential Red Arrow Signals ({len(sell_signals)}):")
        for symbol in sell_signals:
            logging.info(f" - {symbol}")
    else:
        logging.info("No Sell Signals.")

    logging.info(f"Most Recent Market Zone: {latest_zone_color}")
    logging.info("----- End of Trade Signals -----")


# Stock-by-Stock Iteration
def iterate_stocks_individually(algo_connection, cache_connection, start_date, limit=None):

    stock_symbols = fetch_all_stocks(algo_connection, limit)
    if not stock_symbols:
        logging.error("No stocks found in the database.")
        return

    logging.info(f"Fetched {len(stock_symbols)} stock(s).")

    all_zones = load_all_zones(algo_connection)
    if not all_zones:
        logging.warning("No zone data found. Defaulting to 'red' if needed.")

    end_date = datetime.now().strftime("%Y-%m-%d")

    for idx, symbol in enumerate(stock_symbols, start=1):
        logging.info(f"\n=== Processing stock {idx}/{len(stock_symbols)}: {symbol} ===")

        full_data = fetch_data_from_cache(cache_connection, symbol, start_date, end_date)
        if full_data is None or full_data.empty:
            logging.warning(f"No data found for {symbol}. Skipping.")
            continue

        full_data.sort_index(inplace=True)

        unique_dates = sorted(full_data.index.unique())

        for day_idx, current_day in enumerate(unique_dates):
            current_day_str = current_day.strftime('%Y-%m-%d')
            is_today = (day_idx == len(unique_dates) - 1) 

            zone_color = find_zone_for_date(all_zones, current_day)

            daily_data = full_data.loc[:current_day]
            if daily_data.empty:
                continue

            process_stock_data(
                algo_connection=algo_connection,
                cache_connection=cache_connection,
                symbol=symbol,
                start_date=start_date,
                current_date=current_day_str,
                market_zone=zone_color,
                is_today=is_today,
                daily_data=daily_data
            )

    buy_signals, sell_signals = fetch_buy_sell_signals(algo_connection)

    if all_zones:
        latest_zone_color = all_zones[-1]['state_color']
    else:
        latest_zone_color = 'red'

    print_trade_signals(buy_signals, sell_signals, latest_zone_color)

    logging.info("Completed processing all stocks.")


# Main Entry Point
def main():
    """
    1) Run the zones script first, logging red/green transitions for SPY.
    2) Then iterate over stocks individually, using the in-memory zone approach.
    """
    logging.info("Starting Portfolio Management Process.")

    stock_limit = None
    start_date = "2019-10-01"

    # DB connections
    algo_connection = create_connection(
        host=ALGO_DB_CONFIG['host'],
        user=ALGO_DB_CONFIG['user'],
        password=ALGO_DB_CONFIG['password'],
        database=ALGO_DB_CONFIG['database']
    )
    cache_connection = create_connection(
        host=CACHE_DB_CONFIG['host'],
        user=CACHE_DB_CONFIG['user'],
        password=CACHE_DB_CONFIG['password'],
        database=CACHE_DB_CONFIG['database']
    )

    if not (algo_connection and cache_connection):
        logging.error("Failed to create DB connections.")
        return

    try:
        logging.info("Running SPY zone iteration first...")
        iterate_spy_zones(algo_connection, cache_connection, start_date)
        logging.info("Finished computing SPY zones.\n")

        logging.info("Now processing individual stocks with in-memory zone data...")
        iterate_stocks_individually(algo_connection, cache_connection, start_date, limit=stock_limit)

    finally:
        algo_connection.close()
        cache_connection.close()
        logging.info("Closed database connections.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {e}")
