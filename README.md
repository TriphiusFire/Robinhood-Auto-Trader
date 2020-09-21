# Robinhood-Auto-Trader #
Autotrading stocks on Robinhood with Python

This simple trading system uses robin_stocks python api wrapper.

It should work for FRACTIONAL share stock trading and crypto on Robinhood. 

## FILES ##
* credentials.json 
  * put your robinhood login and pw in here
* preferences.json : 
  * x is the dollars per buy, each buy buys fractional shares. 
  * "change" is the factor difference between stock price levels.  ie: 1.05 means price levels are 5% going up from previous price level
  * xCrypto and changeCrypto mean the same for crypto instead of stocks.
* rh_crypto_data 
  * hold the symbol and LTP (last trade price) for each cryptocurrency.  LTP updates by change factor after every trade
* rh_stock_data
  * same, but for stocks.
* cryptoRAT.py
  * the python code for cryptocurrency trading on RH
* stockRAT.py
  * the python code for stock trading on RH
  


