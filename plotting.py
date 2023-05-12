# plots graphs
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.use('TkAgg')
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['font.size'] = 14

PNG_OUT_DIR_NAME = 'png_plots'
CSV_IN_DIR_NAME = 'csv_plots'


def plot_portfolio(portfolio):
    fig, axs = plt.subplots(2, 1, figsize=(10, 10), sharex='all',
                            gridspec_kw={'height_ratios': [2, 1]}, dpi=150)
    # make the plots a little tighter
    plt.subplots_adjust(hspace=0.1)
    # remove minor ticks that appear due to sharex
    for ax in axs:
        ax.tick_params(axis='x', which='minor', bottom=False)
    sp_price = (portfolio['index_price'] / portfolio['index_price'][0] * 100)
    sp_price.plot(ax=axs[0], label='S&P 500 price', lw=1)
    portfolio_val = (portfolio['total_portfolio_value'] /
                     portfolio['total_portfolio_value'][0] * 100)
    portfolio_val.plot(ax=axs[0], label='Total portfolio value', lw=1)
    axs[0].legend(loc='upper left')
    axs[0].axhline(y=100, ls='--', c='black', lw=0.5)
    (portfolio['index_drawdown'] * 100).plot(ax=axs[1], lw=1)
    (portfolio['portfolio_value_drawdown'] * 100).plot(ax=axs[1], lw=1)
    axs[0].set_ylabel('Value (%)')
    axs[1].set_ylabel('Drawdown (%)')
    axs[1].set_xlabel('')
    axs[0].set_title('Total portfolio value compared to the S&P 500')
    plt.savefig(f'portfolio.png', dpi=300)
    plt.show()
    plt.close()


def plot_df(df, symbol, name, strategy, params, save_png=False, show_plot=False):
    if strategy == 'sma':
        fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex='all',
                                gridspec_kw={'height_ratios': [3, 1]}, dpi=150)
    else:
        fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex='all',
                                gridspec_kw={'height_ratios': [3, 1, 1]}, dpi=150)
    # make the plots a little tighter
    plt.subplots_adjust(hspace=0.1)
    # remove minor ticks that appear due to sharex
    for ax in axs:
        ax.tick_params(axis='x', which='minor', bottom=False)
    df['Adj Close'].plot(ax=axs[0], lw=1, label='Price', zorder=3, c='orange')

    # plotting the volume as a bar chart
    axs[1].set_ylabel('Volume ($M)')
    # coloring in the areas of the plot where the symbol is within the universe
    axs[1].fill_between(df.index, 0, (df['Volume']/1_000_000).max(),
                        where=df['in_universe'], facecolor='green',
                        alpha=0.15, label='In universe')
    axs[1].bar(df.index, df['Volume']/1_000_000, color='purple', alpha=0.5,
               label='Daily volume')

    if strategy == 'bb':
        df['percent_b'].plot(ax=axs[2], lw=1, label='%B', c='blue')
        axs[2].axhline(y=params['buy_threshold'], ls='--', c='black', lw=0.5)
        axs[2].axhline(y=params['sell_threshold'], ls='--', c='black', lw=0.5)
        axs[2].set_ylabel('%B')
        df['ma'].plot(ax=axs[0], lw=0.5, label='Bollinger Bands', c='b')
        df['lower_bb'].plot(ax=axs[0], lw=0.5, c='b', label='_nolegend_')
        df['upper_bb'].plot(ax=axs[0], lw=0.5, c='b', label='_nolegend_')
        axs[0].fill_between(df.index, df['lower_bb'], df['upper_bb'],
                            facecolor='b', alpha=0.1)

    if strategy == 'sma':
        df['ma_fast'].plot(ax=axs[0], lw=1, label='Fast moving average', c='blue')
        df['ma_slow'].plot(ax=axs[0], lw=1, label='Slow moving average', c='green')

    if strategy == 'rsi_sma':
        df['rsi'].plot(ax=axs[2], lw=1, label='RSI', c='orange')
        axs[2].set_ylabel('RSI')
        df['ma'].plot(ax=axs[0], lw=1, label='Moving average')
        axs[2].axhline(y=params['oversold'], ls='--', c='black', lw=0.5)

    if strategy == 'macd':
        df['macd'].plot(ax=axs[2], label='MACD', color='blue')
        df['signal'].plot(ax=axs[2], label='Signal', color='#F37021')
        axs[2].bar(df.index, df['hist'], label='_nolegend_', alpha=0.5, color='green')
        axs[2].legend()
        axs[2].set_ylabel('MACD')

    # plot buys and sells as scatter plot points
    buy_dates = df.loc[df['position_size'] > 0].index
    buy_prices = df.loc[df['position_size'] > 0, 'Adj Close']
    axs[0].scatter(buy_dates, buy_prices, marker='^', s=100, c='#3CAEA3',
                   zorder=4, edgecolor='black', label='Buy', lw=0.6)
    sell_dates = df.loc[df['position_size'] < 0].index
    sell_prices = df.loc[df['position_size'] < 0, 'Adj Close']
    axs[0].scatter(sell_dates, sell_prices, marker='v', s=100, c='#F37021',
                   zorder=4, edgecolor='black', label='Sell', lw=0.6)
    # set the labels for the graph
    axs[-1].set_xlabel('')
    # set tilt for dates for strategies without oscillators
    if strategy == 'sma':
        axs[-1].set_xticklabels(axs[-1].get_xticklabels(), rotation=30, ha='right')
    axs[0].set_ylabel('Price ($)')
    # set title to name of stock
    axs[0].set_title(f'{name}')
    axs[0].legend()

    if save_png:
        plt.savefig(f'{PNG_OUT_DIR_NAME}/{symbol}.png', dpi=300)
    if show_plot:
        plt.show()
    plt.close()
