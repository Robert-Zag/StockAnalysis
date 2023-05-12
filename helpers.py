# helper functions used throughout several modules
import os
from constants import *
from scipy.stats import linregress


# print basic information about backtest
def print_params():
    print(f"strategy: {STRATEGY}")
    print(f"trading start date: {TRADE_START_DATE}")
    print(f"trading end date: {TRADE_END_DATE}")


# compute annualized sharpe ratio
def get_sharpe_ratio(price_column):
    daily_return = price_column.pct_change().dropna()
    mean_return = daily_return.mean()
    std_return = daily_return.std()
    if not std_return > 0:
        return 0
    return mean_return/std_return * (252**0.5)


# compute annualized sortino ratio
def get_sortino_ratio(price_column):
    daily_return = price_column.pct_change().dropna()
    mean_return = daily_return.mean()
    downside = daily_return[daily_return < 0]
    std_downside = downside.std()
    if not std_downside > 0:
        return 0
    return mean_return/std_downside * (252**0.5)


# compute alpha and beta values
def get_alpha_beta(benchmark, asset):
    if not benchmark.index.equals(asset.index):
        raise ValueError("Datasets do not have the same index")
    # calculate returns for both benchmark and security/portfolio
    benchmark_returns = benchmark.pct_change().dropna()
    security_returns = asset.pct_change().dropna()
    # run linear regression
    beta, alpha, _, _, _ = linregress(benchmark_returns, security_returns)
    return alpha, beta


# compute drawdown
def drawdown(price_column):
    running_max = price_column.cummax()
    return (running_max - price_column) / running_max


# create directories if missing, check for data files
def make_dirs():
    for dir_name in [PNG_OUT_DIR_NAME, CSV_OUT_DIR_NAME]:
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
    if not os.path.isfile(f"{DATA_DIR_NAME}/{METADATA_FILE_NAME}") or \
            not os.path.isfile(f"{DATA_DIR_NAME}/{DATA_FILE_NAME}") or \
            not os.path.isfile(f"{DATA_DIR_NAME}/{SP500_DATA_FILE_NAME}"):
        raise ValueError("Download data first")
