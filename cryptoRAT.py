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
    trade = r.order_sell_crypto_by_price(symbol, dollars,'bid_price','gtc')
    print(trade) # comment out when done testing
    return trade['id']

def cancel(ident):
    cancel = r.cancel_crypto_order(ident)
#     print(cancel)
    return cancel

def getOrder(ident):
    order = r.get_crypto_order_info(ident)
    print("Order state: " + order["state"])
    return order
    
def getCryptoSymbolFromOrder(orderid):
    s = r.get_crypto_quote_from_id(r.get_crypto_order_info('3f9b7c53-a608-455d-85bb-1220c1b20c62')['currency_pair_id'])['symbol']
    if(s=="BTCUSD"): return "BTC"
    if(s=="BSVUSD"): return "BSV"
    if(s=="DOGEUSD"): return "DOGE"
    if(s=="LTCUSD"): return "LTC"
    if(s=="ETCUSD"): return "ETC"
    if(s=="ETHUSD"): return "ETH"

############ PROGRAM ###################
    
print("\nRobinhood Auto Trader - CRYPTO\n RAT-C V1.")

realTrading = False

doReal = input("\nFor mock trading just press <enter> to see which crypto *would* be bought or sold right now.  \nFor real trading type <r> and <enter>: ")
if doReal.lower() == 'r': 
    realTrading = True

mockSpend = 0;
mockSell = 0;

xBuy = 0 #dollar amount per trade, set from preferences.json
change = 9999999 #percent change of price levels (going up), set from preferences.json

with open(preferences_file) as pdata:
    d = json.load(pdata)
    xBuy = d["xCrypto"]
    change = d["changeCrypto"]
    up = d["upCrypto"]
xSell = xBuy*pow(change,up)
print("\nBuying amount per level: $"+str(xBuy)+"\nSell amount per level up: $"+str(xSell))    

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

numSymbols = len(d)
# print(numSymbols)

positions = r.get_crypto_positions()

numPositions = len(positions)
quantities = {}

for i in range(0,numPositions):
#     print(positions[i])
#     print(json.dumps(positions[i],indent=1))
    quantities[positions[i]["currency"]["code"]]=float(positions[i]["cost_bases"][0]["direct_quantity"])
    

index = 0
check = {}
#s is symbol, d is the whole rh_stock_data json dictionary
for s in d:
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
        print("\nBuying "+s+"...\n")        
        if realTrading:
            orderid = (buy(s,xBuy),"buyLow")
            time.sleep(5)
            if getOrder(orderid[0])["state"] == "filled":
                d[s]=Ltp/change
                print("Buy order filled :)")
                with open(crypto_file,'w') as outfile:
                    json.dump(d,outfile)  
            else:
                if getOrder(orderid[0])["state"]=="queued": cancel(orderid[0]) 
                check[s]=orderid
        else: mockSpend+=xBuy
        
    #selling
    if Bid > Ltp*pow(change,up): 
        print("\nSelling "+s+" if sufficient quantity, otherwise buy...\n")
        
        if(s in quantities):
            if(quantities[s]*Bid>xSell):                
                if realTrading:
                    orderid = (sell(s,xSell),"sellHigh")
                    time.sleep(5)
                    if getOrder(orderid[0])["state"] == "filled":
                        d[s]=Ltp*change
                        print("Sell order filled :)")
                        with open(crypto_file,'w') as outfile:
                            json.dump(d,outfile)  
                    else:
                        if getOrder(orderid[0])["state"]=="queued": cancel(orderid[0]) 
                        check[s]=orderid
                else: mockSell+=xSell
            else:
                print("Not enough crypto to sell, buying more instead...")
                if realTrading:
                    orderid = (buy(s,xBuy),"buyHigh")
                    time.sleep(5)
                    if getOrder(orderid[0])["state"] == "filled":
                        d[s]=Ltp*pow(change,up)
                        print("re-up Buy order filled\n")
                        with open(crypto_file,'w') as outfile:
                            json.dump(d,outfile)
                    else:
                        if getOrder(orderid[0])["state"]=="queued": cancel(orderid[0]) 
                        check[s]=orderid
                else: mockSpend+=xBuy  
                        
    
# all the orders that were not filled 5 seconds later
# need to check for filled before saving new LTP
if realTrading:
    while len(check) > 0:
        print("Still not filled: LTP not updated so you may cancel these manually. Once all filled or cancelled this loop ends.  Trying again in 15 seconds...")
        done = []   
        for tup in check:
            s = getCryptoSymbolFromOrder(tup[0])
            print("checking: "+tup)
            order = getOrder(tup[0])
            if order["state"] == "filled":
                Ltp = d[s]
                if order["side"] == "buy": 
                    if(tup[1]=="buyLow"):
                        d[s]=Ltp/change
                    if(tup[1]=="buyHigh"):
                        d[s]=Ltp*pow(change,up)
                if order["side"] == "sell":
                    d[s]=Ltp*change
                with open(crypto_file,'w') as outfile:
                            json.dump(d,outfile) 
                done.append(tup)
            if order["state"] == "cancelled" or order["state"] == "canceled": 
                done.append(tup)
        if len(done) > 0:
            for d in done:
                del check[d]
        print("Still not filled: LTP not updated so you may cancel these manually. Once all filled or cancelled this loop ends.  Trying again in 15 seconds...")
        time.sleep(15)
        print(check)
else:
    print("\nSpend amount would be: "+str(mockSpend))
    print("Sell amount would be: "+str(mockSell))
            
    
#keep window open till user hits <enter>
input()


