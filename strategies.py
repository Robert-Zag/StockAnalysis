# defines trading strategies
import talib

# TREND-FOLLOWING STRATEGIES


# buy when faster moving average crosses above the slower moving average,
# sell when fast ma crosses below slow
# input: fast_period, slow_period
def sma_cross(df, params):
    df['ma_fast'] = df["Adj Close"].rolling(window=params['fast_period']).mean()
    df['ma_slow'] = df["Adj Close"].rolling(window=params['slow_period']).mean()
    df['buy_condition'] = df['ma_fast'] > df['ma_slow']
    df['sell_condition'] = df['ma_fast'] <= df['ma_slow']
    df.dropna(subset=['ma_slow'], inplace=True)
    return df


# buy when the macd line is above the signal line, otherwise sell
# input: fast_period, slow_period, signal_period
def macd(df, params):
    df['macd'], df['signal'], df['hist'] = talib.MACD(df['Adj Close'],
                                                      fastperiod=params['fast_period'],
                                                      slowperiod=params['slow_period'],
                                                      signalperiod=params['signal_period'])
    df['buy_condition'] = df['macd'] > df['signal']
    df['sell_condition'] = df['macd'] <= df['signal']
    df.dropna(subset=['signal'], inplace=True)
    return df


# MEAN REVERSION STRATEGIES


# buy when price crosses from below the buy threshold % of the %B oscillator,
# sell when crosses above sell threshold
# input: period, buy_threshold, sell_threshold
def bollinger_bands(df, params):
    df['ma'] = df['Adj Close'].rolling(window=params['period']).mean()
    std = df['Adj Close'].rolling(window=params['period']).std()
    df['lower_bb'] = df['ma'] - (std * 2)
    df['upper_bb'] = df['ma'] + (std * 2)
    df['percent_b'] = (df['Adj Close'] - df['lower_bb']) / \
                      (df['upper_bb'] - df['lower_bb']) * 100
    df['buy_condition'] = (df['percent_b'].shift(1) < params['buy_threshold']) & \
                          (df['percent_b'] > params['buy_threshold'])
    df['sell_condition'] = df['percent_b'] > params['sell_threshold']
    df.dropna(subset=['ma'], inplace=True)
    return df


# buy when rsi crosses from below the oversold threshold,
# sell when price reaches sma
# input: rsi_period, ma_period, oversold
def rsi_sma(df, params):
    df['rsi'] = talib.RSI(df['Adj Close'], timeperiod=params['rsi_period'])
    df['ma'] = df['Adj Close'].rolling(window=params['ma_period']).mean()
    df['buy_condition'] = (df['rsi'].shift(1) < params['oversold']) & \
                          (df['rsi'] >= params['oversold']) & \
                          (df['Adj Close'] < df['ma'])
    df['sell_condition'] = df['Adj Close'] >= df['ma']
    df.dropna(subset=['ma', 'rsi'], inplace=True)
    return df
