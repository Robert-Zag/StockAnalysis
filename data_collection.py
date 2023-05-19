# a script that has to be run first, gets S&P constituents from wikipedia, downloads data from yfinance
import pandas as pd
import numpy as np
import time
import requests
import yfinance as yf
from constants import *
import os

DOWNLOAD_DATA_START = dt.datetime(year=2000, month=1, day=1)
DOWNLOAD_DATA_END = dt.datetime(year=2023, month=1, day=1)


# create directories if missing
for dir_name in [DATA_DIR_NAME, DATA_DIR_NAME + "/" + IND_DATA_DIR_NAME]:
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)

# create metadata if not present
if not os.path.isfile(f"{DATA_DIR_NAME}/{METADATA_FILE_NAME}"):
    # get all tickers of sp 500
    wiki_html = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    sp500_components = wiki_html[0]
    sp500_changes = wiki_html[1]

    # extract metadata from wikipedia
    columns = ["symbol", "date_added_sp", "name_wiki"]
    data = {}
    for col in columns:
        data[col] = []

    # list through the added sp 500 stocks
    for i in range(len(sp500_changes.index)):
        row = sp500_changes.loc[i]
        data["symbol"] += [row["Added"]["Ticker"]]
        data["date_added_sp"] += [pd.to_datetime(row["Date"]["Date"])]
        data["name_wiki"] += [row["Added"]["Security"]]

    # list through the removed sp 500 stocks
    for i in range(len(sp500_changes.index)):
        row = sp500_changes.loc[i]
        data["symbol"] += [row["Removed"]["Ticker"]]
        data["date_added_sp"] += [np.nan]
        data["name_wiki"] += [row["Removed"]["Security"]]

    # list through the current sp 500 stocks
    for i in range(len(sp500_components.index)):
        row = sp500_components.loc[i]
        data["symbol"] += [row["Symbol"]]
        try:
            data["date_added_sp"] += [pd.to_datetime(row["Date added"])]
        except Exception as _:
            data["date_added_sp"] += [np.nan]
        data["name_wiki"] += [row["Security"]]

    mdf = pd.DataFrame(data, columns=columns)
    mdf = mdf.dropna(subset=["symbol", "name_wiki"])

    # dropping duplicate symbols but keeping the one that has the earlier date
    mdf = mdf.sort_values('date_added_sp')
    mdf = mdf.drop_duplicates(subset=['symbol'], keep='first')
    mdf = mdf.reset_index(drop=True).set_index('symbol')
else:
    print("found metadata in csv, reading...")
    mdf = pd.read_csv(f"{DATA_DIR_NAME}/{METADATA_FILE_NAME}", parse_dates=["date_added_sp"], index_col=0)

# if there is no data, download it
if not os.path.isfile(f"{DATA_DIR_NAME}/{DATA_FILE_NAME}"):
    end_date = DOWNLOAD_DATA_END
    start_date = DOWNLOAD_DATA_START
    df = yf.download(list(mdf.index), start=start_date, end=end_date, interval="1d", group_by='ticker')
    df.to_csv(f"{DATA_DIR_NAME}/{DATA_FILE_NAME}")
else:
    print("found stock price data in csv, reading...")
df = pd.read_csv(f"{DATA_DIR_NAME}/{DATA_FILE_NAME}", parse_dates=True, index_col=[0], header=[0, 1])


# if there is no s&p 500 data, download it
if not os.path.isfile(f"{DATA_DIR_NAME}/{SP500_DATA_FILE_NAME}"):
    end_date = DOWNLOAD_DATA_END
    start_date = DOWNLOAD_DATA_START
    spdf = yf.download("^GSPC", start=start_date, end=end_date, interval="1d", group_by='ticker')
    spdf.to_csv(f"{DATA_DIR_NAME}/{SP500_DATA_FILE_NAME}")
else:
    print("found S&P 500 price data in csv, reading...")
spdf = pd.read_csv(f"{DATA_DIR_NAME}/{SP500_DATA_FILE_NAME}", parse_dates=True, index_col=[0])

# drop empty dfs, empty rows, useless columns
all_symbols = list(set([t[0] for t in df.columns]))
dfs = {}
for ticker in all_symbols:
    ticker_df = df[ticker].dropna(subset=['Adj Close'])
    if not ticker_df.empty:
        ticker_df.to_csv(f"{DATA_DIR_NAME}/{IND_DATA_DIR_NAME}/{ticker}.csv")
        dfs[ticker] = ticker_df
all_symbols = list(dfs.keys())

if not os.path.isfile(f"{DATA_DIR_NAME}/{METADATA_FILE_NAME}"):
    # add more metadata
    mdf['name_yf'] = np.nan
    mdf['currency'] = np.nan
    mdf['exchange'] = np.nan
    mdf['quote_type'] = np.nan
    mdf['timezone'] = np.nan

    for i, symbol in enumerate(all_symbols):
        print(f"Downloading metadata for {symbol} {i+1}/{len(all_symbols)}")
        ticker = yf.Ticker(symbol)
        company_info = ticker.fast_info
        try:
            company_name = ticker.info['longName'] + f" ({symbol})"
            print(f"full company name (symbol): {company_name}")
        except Exception as _:
            company_name = symbol
        mdf.loc[symbol, 'name_yf'] = company_name
        mdf.loc[symbol, 'currency'] = company_info['currency']
        mdf.loc[symbol, 'exchange'] = company_info['exchange']
        mdf.loc[symbol, 'quote_type'] = company_info['quoteType']
        mdf.loc[symbol, 'timezone'] = company_info['timezone']
    mdf = mdf.dropna(subset=['timezone'])
    mdf.to_csv(f"{DATA_DIR_NAME}/{METADATA_FILE_NAME}")
