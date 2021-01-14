import robin_stocks as r
import json
import time
from os.path import isfile 

############ JSON FILES ##################

crypto_file = "./rh_crypto_data.json"  # cryptocurrency symbols / LTP's - NOT IMPLEMENTED
preferences_file="./preferences.json"  # customize trade levels and buy amount
credentials_file= "./credentials.json" # login and password

############ FUNCTIONS ###################
    
#this is the price a market buy would trigger at
def ask(symbol): #test: works
    return float(r.get_crypto_quote(symbol)['ask_price'])

#this is the price a market sell would trigger at
def bid(symbol): #test: works
    return float(r.get_crypto_quote(symbol)['bid_price'])
#test
# print('ASM bid: ',bid(test_symbol))

#buy x worth of stock, returns the trade id
def buy(symbol,dollars):
    print("Buying $"+str(dollars)+" worth of "+ symbol+"...")
    if(symbol != "DOGE"):
        trade = r.order_buy_crypto_by_price(symbol, dollars,'ask_price','gtc')
    else:
        trade = r.order_buy_crypto_by_quantity(symbol, int(dollars/ask(symbol)), 'ask_price', 'gtc')
    print(trade) # comment out when done testing
    return trade['id']
    
#sell x*change worth of stock, returns the trade id
def sell(symbol,dollars):
    print("Selling "+str(dollars)+" of "+ symbol+"...")
    if(symbol != "DOGE"):
        trade = r.order_sell_crypto_by_price(symbol, dollars,'bid_price','gtc')
    else:
        trade = r.order_sell_crypto_by_quantity(symbol, int(dollars/bid(symbol)), 'bid_price', 'gtc')
    print(trade) # comment out when done testing
    return trade['id']

def cancel(ident):
    cancel = r.cancel_crypto_order(ident)
#     print(cancel)
    return cancel

def getOrder(ident):
    order = r.get_crypto_order_info(ident)
    #print("Order " + order)
    return order
    
def getCryptoSymbolFromOrder(orderid):
    s = r.get_crypto_quote_from_id(r.get_crypto_order_info(orderid)['currency_pair_id'])['symbol']
    if(s=="BTCUSD"): return "BTC"
    if(s=="BSVUSD"): return "BSV"
    if(s=="DOGEUSD"): return "DOGE"
    if(s=="LTCUSD"): return "LTC"
    if(s=="ETCUSD"): return "ETC"
    if(s=="ETHUSD"): return "ETH"
    
def countLevelsUp(previousPrice,currentPrice,factor):
    levels = 0
    previousPrice *= factor
    while previousPrice < currentPrice:
        levels+=1
        previousPrice *= factor
    return levels

def countLevelsDown(previousPrice,currentPrice,factor):
    levels = 0
    previousPrice /= factor
    while previousPrice > currentPrice:
        levels+=1
        previousPrice /= factor
    return levels

############ PROGRAM ###################
    
print("\nRobinhood Auto Trader - CRYPTO\n RAT-C V1.")

realTrading = False

doReal = input("\nFor mock trading just press <enter> to see which crypto *would* be bought or sold right now.  \nFor real trading type <r> and <enter>: ")
if doReal.lower() == 'r': 
    realTrading = True



xBuy = 0 #dollar amount per trade, set from preferences.json
change = 9999999 #percent change of price levels (going up), set from preferences.json

with open(preferences_file) as pdata:
    d = json.load(pdata)
    xBuy = d["xCrypto"]
    change = d["changeCrypto"]
    up = d["upCrypto"]

print("\nBuying amount per level: $"+str(xBuy)) 

if isfile(credentials_file):
    with open(credentials_file) as cdata:
        d = json.load(cdata)
        rh_username = d["login"]
        rh_password = d["pw"]
#         print("\nLOGIN DUMP:")
#         print(r.login(rh_username,rh_password))
        r.login(rh_username,rh_password)
else:
    rh_username = input("Enter Robinhood login: ")
    rh_password = input("Enter Robinhood Password: ") 
#     print("\nLOGIN DUMP:")
#     print(r.login(rh_username,rh_password))
    r.login(rh_username,rh_password)


d = None;

if not isfile(crypto_file):
    print("\nYou need a file called rh_crypto_data.json in the RAT folder.")
    print("This file stores a dictionary containing your crypto symbols and the last price you traded each at")
    print('\nJSON data looks like {"SYM1":1.11, "SYM2":50.49} where each "symbol":price pair is comma separated with no comma after the last pair and with all pairs inside curly brackets {...}')
    ans = input("Press <Enter> when you have created rh_crypto_data.json.json in the RAT folder")

print("\nrh_crypto_data.json in the RAT folder looks like...\n")
with open(crypto_file) as json_data:
    d = json.load(json_data)
    print(json.dumps(d, indent=1))
input("\nYour cryptos and the last trade prices of each on your account?\n\n<enter> if everything looks correct.\n")

#how many symbols are being traded
numSymbols = len(d)
# print(numSymbols)

positions = r.get_crypto_positions()

numPositions = len(positions)
quantities = {}

for i in range(0,numPositions):
#     print(positions[i])
#     print(json.dumps(positions[i],indent=1))
    quantities[positions[i]["currency"]["code"]]=float(positions[i]["cost_bases"][0]["direct_quantity"])
    

mockSpend = 0;
mockSell = 0;
index = 0
check = {}
#s is symbol, d is the whole rh_stock_data json dictionary
for s in d:
    try:
        if s in quantities:
            print("\n"+s+" crypto sellable: "+str(quantities[s]))
    #     print("\n"+s+" last trade price: "+str(d[s]))
        Ltp = d[s]
    #     print(s+" Ask: "+str(ask(s)))
        Ask = ask(s)
    #     print(s+" Bid: "+str(bid(s)))
        Bid = bid(s)
        
        #buying
        if Ask < Ltp/change:
            levelsDown = countLevelsDown(Ltp, Ask, change)
            print("\nPrice has fallen by "+str(levelsDown)+" levels")
            print("\nBuying "+str(xBuy*levelsDown)+" worth of "+s+"...\n")        
            if realTrading:
                orderid = (buy(s,xBuy*levelsDown),"buyLow",levelsDown)
                time.sleep(5)
                if getOrder(orderid[0])["state"] == "filled":
                    d[s]=Ltp*pow(1.0/change,levelsDown)
                    print("Buy order filled :)")
                    with open(crypto_file,'w') as outfile:
                        json.dump(d,outfile)  
                else:
                    #if getOrder(orderid[0])["state"]=="queued": cancel(orderid[0]) 
                    check[s]=orderid
            else: mockSpend+=xBuy*levelsDown
            
        #selling / price up : sell or reup buy
        if Bid > Ltp*pow(change,up): 
            levelsUp = countLevelsUp(Ltp, Bid, change)
            print("\nPrice has risen by "+str(levelsUp)+" levels")
            xSell = xBuy*pow(change,levelsUp)
            print("\nSelling "+str(xSell)+" worth of "+s+" if sufficient quantity, otherwise buy...\n")   
                  
            if(s in quantities):
                if(quantities[s]*Bid>=xSell):                
                    if realTrading:
                        orderid = (sell(s,xSell),"sellHigh",levelsUp)
                        time.sleep(5)
                        if getOrder(orderid[0])["state"] == "filled":
                            d[s]=Ltp*change
                            print("Sell order filled :)")
                            with open(crypto_file,'w') as outfile:
                                json.dump(d,outfile)  
                        else:
                            #if getOrder(orderid[0])["state"]=="queued": cancel(orderid[0]) 
                            check[s]=orderid
                    else: mockSell+=xSell
                else: #re-up will be 5x basic buy amount for now
                    print("\nNot enough crypto to sell, buying more instead...")
                    if realTrading:
                        print("\nBuying $"+str(xBuy*5)+" worth of "+s+"...") 
                        orderid = (buy(s,xBuy*5),"buyHigh",levelsUp)
                        time.sleep(5)
                        if getOrder(orderid[0])["state"] == "filled":
                            d[s]=Ask
                            print("\nre-up Buy order filled")
                            with open(crypto_file,'w') as outfile:
                                json.dump(d,outfile)
                        else:
                            if getOrder(orderid[0])["state"]=="queued": cancel(orderid[0]) 
                            check[s]=orderid
                    else: mockSpend+=xBuy*5  
    except:
        print("\nerror\n")
    print("\n*********************")  
                        
    
# all the orders that were not filled 5 seconds later
# need to check for filled before saving new LTP
if realTrading:
    done = [] 
    while len(check) > len(done):
        try:
            print("\nStill not filled: LTP not updated so you may cancel these manually. Once all filled or cancelled this loop ends.  Trying again in 15 seconds...")
            for tup in check:
                print(check)
                print(check[tup][0])
                s = getCryptoSymbolFromOrder(check[tup][0])
                time.sleep(5);
                order = getOrder(check[tup][0])
                print(order);
                if order["state"] == "filled":
                    Ltp = d[s]
                    if order["side"] == "buy": 
                        if(check[tup][1]=="buyLow"):
                            d[s]=Ltp/pow(change,check[tup][2])
                        if(check[tup][1]=="buyHigh"):
                            d[s]=ask(s)
                    if order["side"] == "sell":
                        d[s]=Ltp*change
                    with open(crypto_file,'w') as outfile:
                                json.dump(d,outfile) 
                    done.append(tup)
                if order["state"] == "cancelled" or order["state"] == "canceled" or order["state"] == "filled": 
                    done.append(tup)        
            print("Still not filled: LTP not updated so you may cancel these manually. Once all filled or cancelled this loop ends.  Trying again in 15 seconds...")
            time.sleep(15)
        except: print("\nerror...\n")
else:
    print("\nSpend amount would be: "+str(mockSpend))
    print("Sell amount would be: "+str(mockSell))
            
print("\nDONE\n")


#keep window open till user hits <enter>
input()
