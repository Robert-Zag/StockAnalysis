# constants used across multiple different scripts
import strategies
import datetime as dt

STRATEGY = 'sma'
DATA_START_DATE = dt.datetime(year=2009, month=1, day=1)
TRADE_START_DATE = dt.datetime(year=2020, month=1, day=1)
TRADE_END_DATE = dt.datetime(year=2023, month=1, day=1)

UNIVERSE_SIZE = 50
STARTING_CAPITAL = 100
POSITION_SIZE_QUOTE = 5
TRANSACTION_FEE_AND_SLIPPAGE_PERCENT = 0.1
FEE_FACTOR = (100 - TRANSACTION_FEE_AND_SLIPPAGE_PERCENT) / 100
STOPLOSS_PERCENTAGE = 15

DATA_DIR_NAME = 'stock_price_data'
DATA_FILE_NAME = 'stock_price_data.csv'
METADATA_FILE_NAME = 'stock_price_metadata.csv'
SP500_DATA_FILE_NAME = 'sp500_price_data.csv'
PNG_OUT_DIR_NAME = 'png_plots'
CSV_OUT_DIR_NAME = 'csv_plots'
IND_DATA_DIR_NAME = 'individual_stock_price_data'
COLUMNS = ['usd_holdings', 'stock_holdings_value', 'index_price']

string_to_strategy = {'sma': strategies.sma_cross,
                      'macd': strategies.macd,
                      'bb': strategies.bollinger_bands,
                      'rsi_sma': strategies.rsi_sma}
