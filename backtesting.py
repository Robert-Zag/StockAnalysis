# backtests trading strategies and evaluates metrics
import pandas as pd
import numpy as np
import plotting
from constants import *
from helpers import *

MAKE_CSVS = True
MAKE_PNGS = True
PLOT_PORTFOLIO = True

# optimized strategy parameters (optimized on 2010 - 2020 data)
if STRATEGY == 'sma':
    params = {'fast_period': 23, 'slow_period': 77}
elif STRATEGY == 'macd':
    params = {'fast_period': 49, 'slow_period': 57, 'signal_period': 22}
elif STRATEGY == 'bb':
    params = {'period': 35, 'buy_threshold': 41, 'sell_threshold': 96}
elif STRATEGY == 'rsi_sma':
    params = {'ma_period': 76, 'rsi_period': 23, 'oversold': 46}
else:
    raise ValueError("Invalid strategy")


# populate and format dataframes with data from csvs
def get_data():
    # stock metadata
    metadata = pd.read_csv(f"{DATA_DIR_NAME}/{METADATA_FILE_NAME}",
                           parse_dates=["date_added_sp"], index_col=0)
    # dataframe with price stock data
    df = pd.read_csv(f"{DATA_DIR_NAME}/{DATA_FILE_NAME}",
                     parse_dates=True, index_col=[0], header=[0, 1])
    # S&P 500 data
    indexdata = pd.read_csv(f"{DATA_DIR_NAME}/{SP500_DATA_FILE_NAME}",
                            parse_dates=True, index_col=[0])

    # get a list of all the dates in the data
    index = df[(df.index >= TRADE_START_DATE) & (df.index <= TRADE_END_DATE)].index

    # drop empty dfs, empty rows, useless columns, and shorten to preserve memory
    all_symbols = list(set([t[0] for t in df.columns]))
    dfs = {}
    for ticker in all_symbols:
        ticker_df = df[ticker].dropna(subset=['Adj Close'])
        ticker_df = ticker_df.drop(['Open', 'High', 'Low', 'Close'], axis=1)
        ticker_df = ticker_df.loc[(ticker_df.index >= DATA_START_DATE) &
                                  (ticker_df.index <= TRADE_END_DATE)]
        if not ticker_df.empty:
            # if the stock data has too many repeating values or very low volume,
            # its probably bad data
            constant_returns_ratio = ticker_df['Adj Close'].\
                pct_change().value_counts(normalize=True).max()
            mean_volume = ticker_df['Volume'].mean()
            is_bad_data = constant_returns_ratio >= 0.3 or mean_volume <= 5000
            if not is_bad_data:
                dfs[ticker] = ticker_df
    all_symbols = sorted(list(dfs.keys()))
    return dfs, index, all_symbols, metadata, indexdata


# populate column for universe selection
def filter_universe(dfs, index, all_symbols, mdf):
    for symbol in all_symbols:
        df = dfs[symbol]
        df['in_universe'] = False
        dfs[symbol] = df

    for date in index:
        today_symbols = []
        # drop all the symbols that do not have data
        for symbol in all_symbols:
            # make sure that you don't consider stocks not yet in S&P
            added_date = mdf.loc[symbol, "date_added_sp"]
            # checking if there is data for the given date
            if date in dfs[symbol].index and not date < added_date:
                today_symbols += [symbol]

        # get the volume of a particular symbol based on the current date
        def get_vol(stock_symbol):
            return dfs[stock_symbol]['Volume'].loc[date]
        today_symbols.sort(reverse=True, key=get_vol)

        today_symbols = today_symbols[:UNIVERSE_SIZE]
        # sets the in_universe column for all the symbols that are in the universe today
        for symbol in today_symbols:
            dfs[symbol].loc[date, 'in_universe'] = True


# backtest trading strategy and strategy parameters
def backtest(dfs, all_symbols, mdf, spdf, index, strategy, params, stoploss_percentage):
    stoploss_factor = (100 - stoploss_percentage) / 100
    start_time_of_backtest = dt.datetime.now()
    # adds necessary indicators, populates the has_position and has_stoploss dict
    has_position, has_stoploss = {}, {}
    for symbol in all_symbols:
        has_position[symbol], has_stoploss[symbol] = False, False
        df = dfs[symbol]
        df['position_size'] = np.nan
        df = strategy(df, params)
        # populate a column that is only true when buy condition
        # explicitly changes from false to true
        df['buy_signal'] = df['buy_condition'] & (~df['buy_condition']).shift(1)
        if not df.empty and df.loc[df.index[0], 'buy_signal']:
            df.loc[df.index[0], 'buy_signal'] = False
        # drop rows that were just used as data for indicators
        df = df[df.index >= TRADE_START_DATE]
        # drop rows of data that happened before a symbol became an index constituent
        added_date = mdf.loc[symbol, "date_added_sp"]
        if added_date > TRADE_START_DATE:
            df = df[df.index >= added_date]
        dfs[symbol] = df

    # a dataframe to keep track of the portfolio
    portfolio = pd.DataFrame(columns=COLUMNS)

    # a list of all symbols that were traded at least once
    all_traded_stocks = []

    # keep track of all the trades that took place
    trades = []
    for i, date in enumerate(index):
        # if it's the first day, set the usd holdings to starting capital
        if i == 0:
            portfolio.loc[date, 'usd_holdings'] = STARTING_CAPITAL
        else:
            portfolio.loc[date, 'usd_holdings'] = portfolio.loc[index[i-1], 'usd_holdings']
        portfolio.loc[date, 'stock_holdings_value'] = 0.0

        # evaluate list of symbols that are long or in the universe
        current_symbols = []
        for s in all_symbols:
            if date in dfs[s].index and (has_position[s] or
                                         dfs[s].loc[date, 'in_universe']):
                current_symbols += [s]

        # compute the trades
        for symbol in current_symbols:
            df = dfs[symbol]
            row = df.loc[date]
            it_is_the_last_day = date == dfs[symbol].index[-1]

            # check for buys
            has_enough_cash = portfolio.loc[date, 'usd_holdings'] >= POSITION_SIZE_QUOTE
            allow_buys = not has_position[symbol] and not it_is_the_last_day
            if allow_buys and row['buy_signal'] and has_enough_cash:
                df.loc[date, 'position_size'] = 1
                # adjust usd holdings and position size keeping fees in mind
                portfolio.loc[date, 'usd_holdings'] -= POSITION_SIZE_QUOTE
                has_position[symbol] = (POSITION_SIZE_QUOTE / df.loc[date, 'Adj Close']) *\
                                        FEE_FACTOR
                has_stoploss[symbol] = df.loc[date, 'Adj Close'] * stoploss_factor

                trades += [{'symbol': symbol,
                            'side': 'buy',
                            'price': df.loc[date, 'Adj Close'],
                            'size': df.loc[date, 'position_size'],
                            'date': date}]

                # keep track of all the symbols that have had a trade
                if symbol not in all_traded_stocks:
                    all_traded_stocks += [symbol]

            # handle sells
            if has_stoploss[symbol]:
                trigger_stoploss_sell = has_stoploss[symbol] >= df.loc[date, 'Adj Close']
            else:
                trigger_stoploss_sell = False
            force_sell = it_is_the_last_day and has_position[symbol]
            if trigger_stoploss_sell or force_sell or \
                    (has_position[symbol] and row['sell_condition']):
                df.loc[date, 'position_size'] = -1
                # adjust usd holdings and position size keeping fees in mind
                portfolio.loc[date, 'usd_holdings'] += (has_position[symbol] *
                                                        df.loc[date, 'Adj Close']) * \
                                                        FEE_FACTOR
                has_position[symbol] = False
                has_stoploss[symbol] = False

                trades += [{'symbol': symbol,
                            'side': 'sell',
                            'price': df.loc[date, 'Adj Close'],
                            'size': df.loc[date, 'position_size'],
                            'date': date}]

            # handle the usd value of owned stock
            if has_position[symbol]:
                portfolio.loc[date, 'stock_holdings_value'] += \
                              has_position[symbol] * df.loc[date, 'Adj Close']

    # check to make sure there are no long positions open
    not_long_list = [not has_position[symbol] for symbol in has_position.keys()]
    if not all(not_long_list):
        raise ValueError("There are open longs at the end of the backtest")

    # calculate the total portfolio value
    portfolio['total_portfolio_value'] = portfolio['usd_holdings'] + \
                                         portfolio['stock_holdings_value']
    # sharpe ratio
    sharpe_ratio = get_sharpe_ratio(portfolio['total_portfolio_value'])
    backtest_duration = dt.datetime.now() - start_time_of_backtest
    print(f"backtest evaluation duration: {backtest_duration}, "
          f"sharpe ratio: {sharpe_ratio}, "
          f"params = {params}, "
          f"stoploss = {stoploss_percentage}")
    return sharpe_ratio, portfolio, all_traded_stocks, trades


if __name__ == "__main__":
    print_params()
    make_dirs()
    dfs, index, all_symbols, mdf, spdf = get_data()
    filter_universe(dfs, index, all_symbols, mdf)

    backtest_result = backtest(dfs, all_symbols, mdf, spdf, index,
                               string_to_strategy[STRATEGY], params,
                               STOPLOSS_PERCENTAGE)
    sharpe_ratio, portfolio, all_traded_stocks, trades = backtest_result

    # calculate other portfolio metrics
    portfolio['index_price'] = spdf.loc[portfolio.index, 'Adj Close']
    portfolio['portfolio_value_drawdown'] = drawdown(portfolio['total_portfolio_value'])
    portfolio['index_drawdown'] = drawdown(portfolio['index_price'])

    # calculate more strategy metrics
    max_drawdown = portfolio['portfolio_value_drawdown'].max()*100
    profit = (portfolio['total_portfolio_value'][-1] -
              portfolio['total_portfolio_value'][0])
    profit_percentage = profit/portfolio['total_portfolio_value'][0] * 100

    if PLOT_PORTFOLIO:
        portfolio.to_csv("portfolio.csv")
        plotting.plot_portfolio(portfolio)

    # plotting the results
    for symbol in all_traded_stocks:
        df = dfs[symbol]
        if MAKE_CSVS:
            print(f"saving file {CSV_OUT_DIR_NAME}/{symbol}.csv")
            df.to_csv(f"{CSV_OUT_DIR_NAME}/{symbol}.csv")

        if MAKE_PNGS:
            print(f"saving picture {PNG_OUT_DIR_NAME}/{symbol}.png")
            plotting.plot_df(df, symbol, mdf.loc[symbol, "name_yf"],
                             STRATEGY, params, save_png=True)

    # after backtest results
    full_trades = []
    won_trades = 0
    # a list of tuples (symbol, total profit)
    symbol_profits = []
    for symbol in all_traded_stocks:
        s_trades = [trade for trade in trades if trade['symbol'] == symbol]
        pairs_of_trades = list(zip(s_trades[::2], s_trades[1::2]))
        total_profit_for_symbol = 1
        for buy, sell in pairs_of_trades:
            if not buy['side'] == 'buy' or not sell['side'] == 'sell':
                # check whether the trades have been paired properly
                raise ValueError("Trades not paired properly")
            profit = 100 * (sell['price'] - buy['price'])/buy['price']
            profit_ratio = 1+(sell['price'] - buy['price'])/buy['price']
            total_profit_for_symbol *= profit_ratio
            full_trades += [{'symbol': symbol,
                             'profit': profit,
                             'buy': buy,
                             'sell': sell}]
            if profit > 0:
                won_trades += 1
        symbol_profits.append((symbol, total_profit_for_symbol))

    profits = [ft['profit'] for ft in full_trades]
    full_trades.sort(reverse=True, key=lambda x: x['profit'])
    symbol_profits.sort(reverse=True, key=lambda x: x[1])

    for i, t in enumerate(full_trades[:20]):
        print(f"{i}. {t['symbol']}, profit: {t['profit']}%, "
              f"buy date: {t['buy']['date']}, "
              f"sell date: {t['sell']['date']}")

    for i, symbol_profit in enumerate(symbol_profits[:20]):
        print(f"{i}. {symbol_profit[0]}, profit: {(symbol_profit[1] - 1) * 100}%")

    print(f'there were {len(full_trades)} trades taken')
    print(f'the average profit % was: {sum(profits) / len(profits)}')

    print("")
    print("S&P 500")
    print(f"sharpe ratio: {get_sharpe_ratio(portfolio['index_price'])}")
    print(f"sortino ratio: {get_sortino_ratio(portfolio['index_price'])}")
    print(f"max drawdown: {portfolio['index_drawdown'].max() * 100}%")
    i_p = portfolio['index_price']
    print(f"profit: {round((i_p[-1] - i_p[0]) / i_p[0] * 100, 2)}%")

    print("")
    print("Trading Strategy")
    winrate_percentage = won_trades / len(full_trades) * 100
    print(f"trade win rate: {round(winrate_percentage, 2)}%")
    print(f"sharpe ratio: {get_sharpe_ratio(portfolio['total_portfolio_value'])}")
    print(f"sortino ratio: {get_sortino_ratio(portfolio['total_portfolio_value'])}")
    alpha, beta = get_alpha_beta(portfolio['index_price'],
                                 portfolio['total_portfolio_value'])
    print(f"beta: {beta}\nalpha: {alpha}")
    print(f"max drawdown: {portfolio['portfolio_value_drawdown'].max() * 100}%")
    tpv = portfolio['total_portfolio_value']
    print(f"profit: {round(((tpv[-1] - tpv[0]) / tpv[0] * 100), 2)}%")
