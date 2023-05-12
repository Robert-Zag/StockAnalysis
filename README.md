# StockAnalysis

Welcome to the StocksTrading repository, a project designed to download stock price data, backtest trading strategies, and optimize these strategies via differential evolution. Leaning on the `yfinance` library, StocksTrading downloads stock price data while applying the `TA-Lib` for calculating various technical analysis indicators. The `differential_evolution` function from the `SciPy` library is used for optimizing trading strategies.

## Key Features

1. **Data Collection**: Leverages the `yfinance` library to download historical stock price data.
2. **Trading Strategies Backtesting**: Executes the `backtesting.py` module to test an array of trading strategies that are outlined in the `strategies.py` module.
3. **Strategy Optimization**: Applies the differential evolution algorithm to optimize parameters of the trading strategies.

## Getting Started

### Prerequisites
Before you get started, ensure you have the following installed:

- Python 3.8 or newer
- Libraries: `TA-Lib`, `Matplotlib`, `Pandas`, `NumPy`, `Requests`, `yfinance`, `SciPy`, and `Multiprocessing`

All the necessary Python packages can be installed by using the `requirements.txt` file included in the repository.

### Installation
1. Clone the StocksTrading repository from GitHub.
2. Use the existing `requirements.txt` file to install all the necessary packages.

## Usage

- **Data Collection**: Run the `data_collection.py` script to download the required stock price data.
- **Trading Strategies Backtesting**: Utilize the `backtesting.py` module to test the trading strategies defined in the `strategies.py` module.
- **Strategy Optimization**: The `differential_evolution.py` script can be executed to optimize the parameters of the trading strategies using a differential evolution algorithm.

## Contributing
Your contributions are greatly valued. Feel free to fork the project, make changes, and open a pull request to propose your enhancements.

## License
The StocksTrading project is distributed under the MIT License. See the `LICENSE` file for more information.

## Contact
For any queries or suggestions, feel free to reach out.

Project Link: [StocksTrading](https://github.com/shot4rz/StocksTrading)

Hope you find the StocksTrading toolkit valuable and it aids in enhancing your trading strategies!
