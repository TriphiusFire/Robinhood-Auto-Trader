# Robinhood-Auto-Trader #
I built a simulator called "Slingshot" - based on this strategy so you can see how powerful this type of trading is on totally random price behavior: https://triphiusfire.nz/slingshot-simulator.html
-------------------------------------------------------------------
1. you need python3 to run this
2. install robin_stocks : https://github.com/jmfernandes/robin_stocks

I have been running this in Eclipse with the python plugin.  
Attempts at compiling to EXE are strange as the computer believes it is being attacked by a "wacatac" trojan, so at this time I just run the python scripts from eclipse. maybe the py2exe compiler is bad, or maybe its a false flag.  i'm not taking chances. any python3 interpreter should work if you properly install robin_stocks first.

FILES

credentials.json : add your robinhood login and password

preferences.json : "x" is the dollar amount per buy, "change" is the factor/scale going up from a previous price for a new price level (1/change would be levels going down), "up" is how many price levels up before selling x+profit worth of stock.  Note that if a price falls by 10 levels before running the bot, it will spend 10x on more coin and drop the last trade price reference down (1/change)^10. The bot will only sell one unit of x+profit at a time, and raise the last trade price by ltp * change, regardless of the actual price.  this results in absolute minimum profits being rare.  
xCrypto, changeCrypto, upCrypto are the same but for cryptocurrencies instead of stocks : CRYPTO BOT NOT READY FOR LIVE TRADING, but the stockRAT has been working flawlessly so you can use that.

rh_stock_data.json :
key value pairs wrapped in {}
{"STOCK1": price, "STOCK2" price}
key/value pairs are separated by comma!

Recommendation: 
1. pick X, maybe that's 1 dollar, 20 dollars, whatever
2. manually buy 5X worth of every stock you want to auto-trade
3. record the ticker and price you bought each stock at in rh_stock_data.json
4. Once a day, Monday through Friday run the bot! 

in 1 year i have earned around 80% profit with this simple strategy
