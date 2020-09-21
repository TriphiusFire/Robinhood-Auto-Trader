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
  
## HOW IT WORKS ##
If the current ask price of a stock or crypto is lower than the number in the rh_crypto|stock_data.json file associated with that symbol divided by the change factor from preferences.json, the bot will spend X dollars (also specified in preferences.json) on more fractional share stock. Same on Crypto, exception: DOGE coin only allows whole amounts of DOGE to be bought. Other cryptos, as of today, all allow fractional amounts.

If the current bid price is higher than the number in the rh data json by the change factor then if there is enough to sell X * change worth of stock we will, otherwise we will buy more stock and update the price in the appropriate json data file.

After each trade the price in the rh_crypto|stock_data.json is scaled up or down by the change factor depending if the order was a buy or sell.

Example: with change = 1.05 the price levels go up buy 5% and down by price/1.05.  if X = 5 dollars then each sell will generate at least 25 cents. how will this work in the long run? is it actuall possible to make money? consider, if a price goes down 10 levels and you bought another $5 of asset at each level going down, the "loss" is 55 levels (summation of integers 1 to 10), and so it would take a maximum of 55 price wiggles up and down 1 level to make up for the loss of the ten price level falls.  Everything after that is pure profit.

basically, over the long run, always buying low and selling high, and understanding that price overlap over time is always stronger than direct up or down movement.  

buy low, sell high, no exceptions. it works. 


