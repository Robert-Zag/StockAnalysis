# optimize parameters of trading strategies using differential evolution
import backtesting
from helpers import *
from scipy.optimize import differential_evolution
import multiprocessing as mp


# tell the progress of the optimization at the end of each generation
def progress_callback(xk, convergence):
    print("Current best solution:", xk)
    print("Current convergence value:", convergence)


# evaluates the fitness of the input parameters
def objective_function(params, *args):
    dfs, all_symbols, mdf, spdf, index, strat_dict, param_bounds = args
    param_names = param_bounds[STRATEGY][0]
    formatted_params = {param_names[i]: round(params[i]) for i in range(len(param_names))}
    dfs_copy = {key: value.copy(deep=True) for key, value in dfs.items()}
    if STRATEGY in ['sma', 'macd']:
        # penalize if fast period is larger than slow period
        if formatted_params['fast_period'] >= formatted_params['slow_period']:
            return 1_000_000
    # perform the backtest
    backtest_result = backtesting.backtest(dfs_copy, all_symbols, mdf, spdf,
                                           index, strat_dict[STRATEGY], formatted_params,
                                           STOPLOSS_PERCENTAGE)
    sharpe_ratio, portfolio, all_traded_stocks, trades = backtest_result
    # penalize strategy if there is less than one trade a year on average
    day_count = len(portfolio.index)
    buy_count = int(len(trades) / 2)
    if buy_count/day_count*252 <= 1:
        print(f"Entered {buy_count} positions over a period of {day_count} days. "
              f"On average that's {buy_count / day_count * 252} entries a year.")
        return 1_000_000
    # penalize low or no sharpe ratio
    if not sharpe_ratio > 0:
        return 1_000_000
    return -sharpe_ratio


if __name__ == "__main__":
    # for MacOS or Linux, set the start method for multiprocessing
    mp.set_start_method('fork')
    print_params()
    dfs, index, all_symbols, mdf, spdf = backtesting.get_data()
    backtesting.filter_universe(dfs, index, all_symbols, mdf)
    param_bounds = {'sma': (['fast_period', 'slow_period'], [(5, 50), (10, 100)]),
                    'macd': (['fast_period', 'slow_period', 'signal_period'],
                             [(5, 50), (10, 100), (5, 50)]),
                    'bb': (['period', 'buy_threshold', 'sell_threshold'],
                           [(10, 100), (0, 49), (51, 100)]),
                    'rsi_sma': (['ma_period', 'rsi_period', 'oversold'],
                                [(10, 100), (5, 50), (0, 49)])}

    # run the optimization
    num_workers = os.cpu_count()
    print(f"initiating optimization with {num_workers} workers")
    result = differential_evolution(objective_function,
                                    param_bounds[STRATEGY][1],
                                    args=(dfs, all_symbols, mdf, spdf, index,
                                          string_to_strategy, param_bounds),
                                    seed=69420,
                                    callback=progress_callback,
                                    workers=num_workers,
                                    updating='deferred')

    # print optimized parameters
    for i, param_name in enumerate(param_bounds[STRATEGY][0]):
        param_name = param_name.replace('_', ' ')
        print(f'optimized {param_name}: {result.x[i]}')
    print(f'-----\n{result}')
