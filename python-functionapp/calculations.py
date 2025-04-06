import logging
import pyodbc
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pandas as pd
import os
import sys

# Setup enhanced logging for Azure Functions
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("calculations_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Database configuration from environment variables
ALGO_DB_CONFIG = {
    'host': os.getenv('ALGO_DB_HOST'),
    'user': os.getenv('ALGO_DB_USER'),
    'password': os.getenv('ALGO_DB_PASSWORD'),
    'database': 'algo_data'
}

CACHE_DB_CONFIG = {
    'host': os.getenv('CACHE_DB_HOST'),
    'user': os.getenv('CACHE_DB_USER'),
    'password': os.getenv('CACHE_DB_PASSWORD'),
    'database': 'cache'
}

# --------------------------------------------------------------------------------
# Utility Functions (integrated from utils.py)
# --------------------------------------------------------------------------------

def create_connection(host, user, password, database):
    """
    Create a database connection using pyodbc for SQL Server.
    """
    try:
        # Log available ODBC drivers for troubleshooting
        logging.debug("Available ODBC drivers:")
        for driver in pyodbc.drivers():
            logging.debug(f"  - {driver}")

        # Try to determine the best driver to use
        preferred_drivers = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]
        
        selected_driver = None
        for driver in preferred_drivers:
            if driver in pyodbc.drivers():
                selected_driver = driver
                logging.debug(f"Selected driver: {driver}")
                break
        
        if not selected_driver:
            available_drivers = pyodbc.drivers()
            if available_drivers:
                selected_driver = available_drivers[0]
                logging.debug(f"No preferred driver found. Using: {selected_driver}")
            else:
                logging.error("No ODBC drivers found on this system")
                return None

        # Construct connection string for SQL Server
        conn_str = (
            f"DRIVER={{{selected_driver}}};"
            f"SERVER={host},1433;"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
        )
        
        logging.debug(f"Connection string (without password): DRIVER={{{selected_driver}}};SERVER={host},1433;DATABASE={database};UID={user};PWD=***")
        
        connection = pyodbc.connect(conn_str)
        logging.info(f"Connected to SQL Server on database '{database}' using pyodbc.")
        return connection
    except pyodbc.Error as e:
        logging.error(f"Error while connecting to SQL Server database '{database}': {e}")
        if len(e.args) > 1:
            logging.error(f"Error details: {e.args[1]}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while connecting to database '{database}': {e}")
        return None

def is_trading_day(date):
    """
    Check if a given date is a trading day (Monday to Friday).
    """
    return date.weekday() < 5  # Monday to Friday are trading days

# --------------------------------------------------------------------------------
# Basic Utilities
# --------------------------------------------------------------------------------

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
    except (InvalidOperation, ValueError) as e:
        logging.error(f"Error converting value to Decimal: {e} | Value: {value}")
        return None

# --------------------------------------------------------------------------------
# Data Fetching Functions
# --------------------------------------------------------------------------------

def fetch_data_from_cache(connection, symbol, start_date, end_date):
    """
    Fetch stock data from cache database.
    Adapted for SQL Server syntax.
    """
    try:
        cursor = connection.cursor()
        table_name = f"{symbol}_cache"
        
        # Check if table exists
        cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}'")
        if cursor.fetchone()[0] == 0:
            logging.warning(f"Table {table_name} does not exist in cache database.")
            return None
            
        query = f"""
            SELECT [date], [open], [high], [low], [close], [volume], [split_factor]
            FROM {table_name}
            WHERE [date] BETWEEN ? AND ?
            ORDER BY [date] ASC
        """
        
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        
        if not rows:
            logging.warning(f"No data found for {symbol} between {start_date} and {end_date}.")
            return None
            
        # Convert to DataFrame
        data = []
        for row in rows:
            data.append({
                'date': row[0],
                'open': row[1],
                'high': row[2],
                'low': row[3],
                'close': row[4],
                'volume': row[5],
                'split_factor': row[6]
            })
            
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    except pyodbc.Error as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching data for {symbol}: {e}")
        return None

# --------------------------------------------------------------------------------
# Database Fetching & Updating (using pyodbc)
# --------------------------------------------------------------------------------

def fetch_all_stocks(algo_connection, limit=None):
    try:
        cursor = algo_connection.cursor()
        # In SQL Server, use TOP for limiting rows
        if limit is not None:
            query = f"SELECT TOP {limit} symbol FROM stocks ORDER BY symbol ASC"
        else:
            query = "SELECT symbol FROM stocks ORDER BY symbol ASC"
        logging.info(f"Executing SQL Query: {query}")
        cursor.execute(query)
        rows = cursor.fetchall()
        stock_list = [row[0] for row in rows] if rows else []
        logging.info(f"Fetched {len(stock_list)} stock(s).")
        return stock_list
    except Exception as e:
        logging.error(f"Error fetching stocks: {e}")
        return []

def update_all_time_high_info(algo_connection, symbol, new_high, new_high_date):
    """
    Unconditionally update the all_time_high and all_time_high_date for a given symbol.
    """
    try:
        logging.debug(f"Updating all-time high for {symbol} to {new_high} on {new_high_date.date()}.")
        cursor = algo_connection.cursor()
        cursor.execute(
            "UPDATE stocks SET all_time_high = ?, all_time_high_date = ? WHERE symbol = ?",
            (float(new_high), new_high_date.strftime('%Y-%m-%d'), symbol)
        )
        algo_connection.commit()
        logging.info(f"Updated {symbol} all_time_high to {new_high} on {new_high_date.date()}.")
        return new_high, new_high_date
    except Exception as e:
        logging.error(f"Error updating all-time high info for {symbol}: {e}")
        return None, None

def update_trade_signal(algo_connection, symbol, signal):
    """
    Update the trade_signal field in the stocks table for the given symbol.
    """
    try:
        cursor = algo_connection.cursor()
        cursor.execute(
            "UPDATE stocks SET trade_signal = ? WHERE symbol = ?",
            (signal, symbol)
        )
        algo_connection.commit()
        logging.info(f"Updated trade_signal for {symbol} to '{signal}'.")
    except Exception as e:
        logging.error(f"Error updating trade_signal for {symbol}: {e}")

def update_last_trade_signal(algo_connection, symbol, trade_signal):
    """
    Update the last_trade_signal field in the stocks table for the given symbol.
    """
    try:
        cursor = algo_connection.cursor()
        cursor.execute(
            "UPDATE stocks SET last_trade_signal = ? WHERE symbol = ?",
            (trade_signal, symbol)
        )
        algo_connection.commit()
        logging.info(f"Updated last_trade_signal for {symbol} to '{trade_signal}'.")
    except Exception as e:
        logging.error(f"Error updating last_trade_signal for {symbol}: {e}")

def update_anchored_vwap_at_buy(algo_connection, symbol, anchored_vwap):
    """
    Update the anchored_vwap_at_buy field in the stocks table for the given symbol.
    """
    try:
        cursor = algo_connection.cursor()
        cursor.execute(
            "UPDATE stocks SET anchored_vwap_at_buy = ? WHERE symbol = ?",
            (anchored_vwap, symbol)
        )
        algo_connection.commit()
        logging.info(f"Updated anchored_vwap_at_buy for {symbol} to {anchored_vwap}.")
    except Exception as e:
        logging.error(f"Error updating anchored_vwap_at_buy for {symbol}: {e}")

def load_all_zones(algo_connection):
    """
    Fetch all zone changes, sorted by state_change_date ascending.
    Returns a list of dictionaries.
    """
    try:
        cursor = algo_connection.cursor()
        cursor.execute("""
            SELECT state_color, state_change_date
            FROM zone_state
            ORDER BY state_change_date ASC
        """)
        rows = cursor.fetchall()
        zones = []
        for row in rows:
            zones.append({
                'state_color': row[0],
                'state_change_date': pd.to_datetime(row[1])
            })
        return zones
    except Exception as e:
        logging.error(f"Error loading zone states: {e}")
        return []

def fetch_buy_sell_signals(algo_connection):
    """
    Fetch all buy and sell signals from the stocks table.
    """
    try:
        cursor = algo_connection.cursor()
        cursor.execute("SELECT symbol FROM stocks WHERE trade_signal = 'BUY'")
        buy_rows = cursor.fetchall()
        buy_signals = [row[0] for row in buy_rows] if buy_rows else []
        logging.info(f"Total BUY signals: {len(buy_signals)}")

        cursor.execute("SELECT symbol FROM stocks WHERE trade_signal = 'SELL'")
        sell_rows = cursor.fetchall()
        sell_signals = [row[0] for row in sell_rows] if sell_rows else []
        logging.info(f"Total SELL signals: {len(sell_signals)}")

        return buy_signals, sell_signals
    except Exception as e:
        logging.error(f"Error fetching buy/sell signals: {e}")
        return [], []

def print_trade_signals(buy_signals, sell_signals, latest_zone_color):
    """
    Print the lists of buy and sell signals, then print the most recent market zone.
    """
    print("----- Trade Signals -----")
    if buy_signals:
        print(f"Potential Green Arrow Signals ({len(buy_signals)}):")
        for symbol in buy_signals:
            print(f" - {symbol}")
    else:
        print("No Buy Signals.")

    if sell_signals:
        print(f"Potential Red Arrow Signals ({len(sell_signals)}):")
        for symbol in sell_signals:
            print(f" - {symbol}")
    else:
        print("No Sell Signals.")

    print(f"Most Recent Market Zone: {latest_zone_color}")
    print("----- End of Trade Signals -----")

# --------------------------------------------------------------------------------
# Signal Processing Functions
# --------------------------------------------------------------------------------

def calculate_anchored_vwap(data, anchor_date, symbol):
    """
    Calculate anchored VWAP from the anchor date.
    """
    try:
        # Filter data from anchor date onwards
        filtered_data = data[data.index >= anchor_date].copy()
        
        if filtered_data.empty:
            logging.warning(f"No data available for {symbol} from anchor date {anchor_date}")
            return pd.DataFrame()
            
        # Calculate typical price: (high + low + close) / 3
        filtered_data['typical_price'] = (filtered_data['high'] + filtered_data['low'] + filtered_data['close']) / 3
        
        # Calculate cumulative (price * volume)
        filtered_data['price_volume'] = filtered_data['typical_price'] * filtered_data['volume']
        filtered_data['cumulative_price_volume'] = filtered_data['price_volume'].cumsum()
        
        # Calculate cumulative volume
        filtered_data['cumulative_volume'] = filtered_data['volume'].cumsum()
        
        # Calculate VWAP
        filtered_data['vwap'] = filtered_data['cumulative_price_volume'] / filtered_data['cumulative_volume']
        
        return filtered_data
    except Exception as e:
        logging.error(f"Error calculating anchored VWAP for {symbol}: {e}")
        return pd.DataFrame()

def find_b_signal(df, symbol, current_date):
    """
    Find a BUY signal in the data up to current_date.
    """
    try:
        # Filter data up to current date
        data = df[df.index <= current_date].copy()
        if len(data) < 3:
            return None
            
        # Check for BUY signal conditions
        for i in range(2, len(data)):
            # Get the last three rows
            last_three = data.iloc[i-2:i+1]
            
            # Conditions for BUY signal
            if (last_three['close'].iloc[2] > last_three['vwap'].iloc[2] and
                last_three['close'].iloc[1] <= last_three['vwap'].iloc[1] and
                last_three['close'].iloc[0] <= last_three['vwap'].iloc[0]):
                
                return last_three.index[2]  # Return the date of the BUY signal
                
        return None
    except Exception as e:
        logging.error(f"Error finding BUY signal for {symbol}: {e}")
        return None

def find_s_signal(df, symbol, current_date):
    """
    Find a SELL signal in the data up to current_date.
    """
    try:
        # Filter data up to current date
        data = df[df.index <= current_date].copy()
        if len(data) < 3:
            return None
            
        # Check for SELL signal conditions
        for i in range(2, len(data)):
            # Get the last three rows
            last_three = data.iloc[i-2:i+1]
            
            # Conditions for SELL signal
            if (last_three['close'].iloc[2] < last_three['vwap'].iloc[2] and
                last_three['close'].iloc[1] >= last_three['vwap'].iloc[1] and
                last_three['close'].iloc[0] >= last_three['vwap'].iloc[0]):
                
                return last_three.index[2]  # Return the date of the SELL signal
                
        return None
    except Exception as e:
        logging.error(f"Error finding SELL signal for {symbol}: {e}")
        return None

def find_two_bar_b_signal(last_four, symbol):
    """
    Find a two-bar BUY signal.
    """
    try:
        if len(last_four) < 2:
            return None
            
        # Get the last two rows
        last_two = last_four.iloc[-2:]
        
        # Conditions for two-bar BUY signal
        if (last_two['close'].iloc[1] > last_two['vwap'].iloc[1] and
            last_two['close'].iloc[0] <= last_two['vwap'].iloc[0]):
            
            return last_two.index[1]  # Return the date of the BUY signal
            
        return None
    except Exception as e:
        logging.error(f"Error finding two-bar BUY signal for {symbol}: {e}")
        return None

def find_two_bar_s_signal(last_four, symbol):
    """
    Find a two-bar SELL signal.
    """
    try:
        if len(last_four) < 2:
            return None
            
        # Get the last two rows
        last_two = last_four.iloc[-2:]
        
        # Conditions for two-bar SELL signal
        if (last_two['close'].iloc[1] < last_two['vwap'].iloc[1] and
            last_two['close'].iloc[0] >= last_two['vwap'].iloc[0]):
            
            return last_two.index[1]  # Return the date of the SELL signal
            
        return None
    except Exception as e:
        logging.error(f"Error finding two-bar SELL signal for {symbol}: {e}")
        return None

def find_zone_for_date(zones_list, target_date):
    """
    Given a sorted list of zones by ascending state_change_date,
    return the zone color that applies to target_date.
    """
    if not zones_list:
        return 'red'  # fallback if no zone data exists
    
    last_color = None
    for row in zones_list:
        if row['state_change_date'] <= target_date:
            last_color = row['state_color']
        else:
            break
    return last_color if last_color else 'red'

# --------------------------------------------------------------------------------
# Core Signal Processing for a Single Stock/Single Date
# --------------------------------------------------------------------------------

def process_stock_data(
    algo_connection,
    cache_connection,
    symbol,
    start_date,
    current_date,
    market_zone,
    is_today=False,
    daily_data=None
):
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
            logging.warning(f"Not enough data points for {symbol}. Needed {MIN_DATA_POINTS}, found {len(data)}. Skipping.")
            return

        current_date_ts = pd.to_datetime(current_date).normalize()

        # Check for stock split
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
                logging.info(f"[SPLIT DETECTED] {symbol} factor={split_factor_today} on {current_date_ts.date()}. Set all_time_high={new_close}, last_trade_signal=BUY. Skipping other signals this day.")
            return

        # Fetch current all-time high info and last_trade_signal
        cursor = algo_connection.cursor()
        cursor.execute("SELECT all_time_high, all_time_high_date, last_trade_signal FROM stocks WHERE symbol = ?", (symbol,))
        result = cursor.fetchone()
        if result and result[0] is not None and result[1] is not None:
            current_all_time_high = safe_decimal_conversion(result[0])
            current_all_time_high_date = pd.to_datetime(result[1])
            last_trade_signal = result[2]
            logging.info(f"Current all-time high for {symbol}: {current_all_time_high}, date: {current_all_time_high_date}, last_signal: {last_trade_signal}")
        else:
            current_all_time_high = safe_decimal_conversion(data.iloc[0]['close'])
            current_all_time_high_date = data.index[0]
            last_trade_signal = None
            updated_high, updated_date = update_all_time_high_info(
                algo_connection, symbol, current_all_time_high, current_all_time_high_date
            )
            if updated_high is None:
                logging.warning(f"Failed to set initial all-time high for {symbol}. Skipping.")
                return
            current_all_time_high, current_all_time_high_date = updated_high, updated_date

        # Calculate Anchored VWAP
        vwap_data = calculate_anchored_vwap(data, anchor_date=current_all_time_high_date, symbol=symbol)
        if vwap_data.empty:
            logging.warning(f"VWAP calculation for {symbol} returned empty data. Skipping.")
            return

        if is_today:
            last_four = vwap_data.tail(4)
            if last_trade_signal == 'BUY':
                s_date = find_two_bar_s_signal(last_four, symbol)
                if s_date:
                    update_trade_signal(algo_connection, symbol, 'SELL')
                    update_last_trade_signal(algo_connection, symbol, 'SELL')
                    logging.info(f"Two-bar SELL signal for {symbol} on {s_date.date()}.")
                else:
                    update_trade_signal(algo_connection, symbol, None)
            else:
                b_date = find_two_bar_b_signal(last_four, symbol)
                if b_date:
                    update_trade_signal(algo_connection, symbol, 'BUY')
                    update_last_trade_signal(algo_connection, symbol, 'BUY')
                    logging.info(f"Two-bar BUY signal for {symbol} on {b_date.date()}.")
                else:
                    update_trade_signal(algo_connection, symbol, None)
        else:
            b_signal_detected = False
            s_signal_detected = False
            if last_trade_signal != 'BUY':
                b_signal_date = find_b_signal(df=vwap_data, symbol=symbol, current_date=current_date_ts)
                if b_signal_date:
                    b_signal_date = pd.to_datetime(b_signal_date)
                    if b_signal_date.date() == current_date_ts.date():
                        b_signal_detected = True
                        update_last_trade_signal(algo_connection, symbol, 'BUY')
            if last_trade_signal == 'BUY':
                s_signal_date = find_s_signal(df=vwap_data, symbol=symbol, current_date=current_date_ts)
                if s_signal_date:
                    s_signal_date = pd.to_datetime(s_signal_date)
                    if s_signal_date.date() == current_date_ts.date():
                        s_signal_detected = True
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
                        update_all_time_high_info(algo_connection, symbol, latest_new_high, latest_new_high_date)

        logging.info(f"Processed signals for {symbol} on {current_date}.")

    except Exception as e:
        logging.error(f"Error processing {symbol} on {current_date}: {e}")

# --------------------------------------------------------------------------------
# Zones Processing
# --------------------------------------------------------------------------------

def iterate_spy_zones(algo_connection, cache_connection, start_date):
    """
    Process SPY data to determine market zones.
    """
    try:
        logging.info("Processing SPY data to determine market zones")
        
        # Fetch SPY data
        spy_data = fetch_data_from_cache(cache_connection, "SPY", start_date, datetime.now().strftime('%Y-%m-%d'))
        if spy_data is None or spy_data.empty:
            logging.error("Failed to fetch SPY data. Cannot determine market zones.")
            return
            
        logging.info(f"Fetched {len(spy_data)} days of SPY data")
        
        # Clear existing zone data
        cursor = algo_connection.cursor()
        cursor.execute("DELETE FROM zone_state")
        algo_connection.commit()
        logging.info("Cleared existing zone_state data")
        
        # Process SPY data to determine zones
        current_zone = 'red'  # Start with red zone
        
        # Calculate 200-day SMA
        spy_data['sma_200'] = spy_data['close'].rolling(window=200).mean()
        
        # Calculate 20-day EMA
        spy_data['ema_20'] = spy_data['close'].ewm(span=20, adjust=False).mean()
        
        for date, row in spy_data.iterrows():
            if pd.notna(row['sma_200']) and pd.notna(row['ema_20']):
                new_zone = 'green' if row['close'] > row['sma_200'] and row['ema_20'] > row['sma_200'] else 'red'
                
                # If zone changed, insert a new record
                if new_zone != current_zone:
                    cursor.execute(
                        "INSERT INTO zone_state (state_color, state_change_date) VALUES (?, ?)",
                        (new_zone, date.strftime('%Y-%m-%d'))
                    )
                    algo_connection.commit()
                    logging.info(f"Zone changed to {new_zone} on {date.strftime('%Y-%m-%d')}")
                    current_zone = new_zone
        
        logging.info("SPY zone processing completed")
        
    except Exception as e:
        logging.error(f"Error processing SPY zones: {e}")

# --------------------------------------------------------------------------------
# Stock-By-Stock Iteration (After Zones Are Computed)
# --------------------------------------------------------------------------------

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

# --------------------------------------------------------------------------------
# Azure Functions Entry Point
# --------------------------------------------------------------------------------

def main(mytimer):
    """Entry point for Azure Functions timer trigger"""
    logging.info(f"Python timer trigger function executed at: {datetime.now()}")
    if mytimer and mytimer.past_due:
        logging.info("The timer is past due!")
    
    try:
        print("----- Trade Signals -----")
        logging.info("Starting Portfolio Management Process.")
        
        stock_limit = None
        start_date = "2019-10-01"
        
        # Create DB connections
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
            print("ERROR: Failed to create database connections.")
            print("----- End of Trade Signals -----")
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
            
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {e}")
        print(f"ERROR: {str(e)}")
        print("----- End of Trade Signals -----")

# For direct execution (not through Azure Functions)
if __name__ == "__main__":
    try:
        # Call main with None to indicate not from timer trigger
        main(None)
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {e}")