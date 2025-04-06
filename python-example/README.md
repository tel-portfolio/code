Algorithmic Trading Signal Processor

This project processes historical and current stock market data to generate algorithmic trading signals using Python. It’s designed to be run as part of an automated trading system. It calculates stock value based on an anchored vwap calculation and looking for certain criteria to be met before a "Buy Signal" or a "Sell Signal" is issued for a stock.

---- What It Does ----

- Loads daily stock data from a MySQL cache
- Evaluates anchored VWAP starting from the last all-time high
- Detects buy and sell signals using custom signal logic
- Tracks market zone state based on SPY behavior
- Stores and updates signals in a MySQL database

All signal functions and market logic are abstracted into separate modules to promote clean, testable design.

---- Disclaimer ----

This script has been scrubbed of all proprietary code. This script is to be used as a Python coding example for the purposes of my portfolio only.

---- Key Components -----

| Module | Purpose |
|--------|---------|
| `main.py` | Coordinates the daily processing loop |
| `utils.py` | Manages secure DB connections |
| `signals.py` | Contains signal detection logic (modular, abstracted) |
| `data_fetching.py` | Loads stock history from the cache DB |
| `zones.py` | Evaluates SPY-based market conditions |

---- Environment Setup ----

The script uses environment variables for secure DB access:

ALGO_DB_HOST=mysql.host
ALGO_DB_USER=username
ALGO_DB_PASSWORD=password
