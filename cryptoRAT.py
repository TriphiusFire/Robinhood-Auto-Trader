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
    xBuy = d["x"]
    change = d["change"]
xSell = xBuy*change
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

# print(r.get_crypto_quote("BTC"))

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
            orderid = buy(s,xBuy)
            time.sleep(5)
            if getOrder(orderid)["state"] == "filled":
                d[s]=Ltp/change
                print("Buy order filled :)")
                with open(crypto_file,'w') as outfile:
                    json.dump(d,outfile)  
            else:
                if getOrder(orderid)["state"]=="queued": cancel(orderid) 
                check[s]=orderid
        else: mockSpend+=xBuy
        
    #selling
    if Bid > Ltp*change: 
        print("\nSelling "+s+" if sufficient quantity, otherwise buy...\n")
        
        if(s in quantities):
            if(quantities[s]*Bid>xSell):                
                if realTrading:
                    orderid = sell(s,xSell)
                    time.sleep(5)
                    if getOrder(orderid)["state"] == "filled":
                        d[s]=Ltp*change
                        print("Sell order filled :)")
                        with open(crypto_file,'w') as outfile:
                            json.dump(d,outfile)  
                    else:
                        if getOrder(orderid)["state"]=="queued": cancel(orderid) 
                        check[s]=orderid
                else: mockSell+=xSell
            else:
                print("Not enough crypto to sell, buying more instead...")
                if realTrading:
                    orderid = buy(s,xBuy)
                    time.sleep(5)
                    if getOrder(orderid)["state"] == "filled":
                        d[s]=Ltp*change
                        print("re-up Buy order filled\n")
                        with open(crypto_file,'w') as outfile:
                            json.dump(d,outfile)
                    else:
                        if getOrder(orderid)["state"]=="queued": cancel(orderid) 
                        check[s]=orderid
                else: mockSpend+=xBuy  
                        
    
# all the orders that were not filled 5 seconds later
# need to check for filled before saving new LTP
if realTrading:
    while len(check) > 0:
        done = []        
        for s in check:
            print("checking: "+s)
            order = getOrder(check[s])
            if order["state"] == "filled":
                Ltp = d[s]
                if order["side"] == "buy":            
                    d[s]=Ltp/change
                if order["side"] == "sell":
                    d[s]=Ltp*change
                with open(crypto_file,'w') as outfile:
                            json.dump(d,outfile) 
                done.append(s)
            if order["state"] == "cancelled" or order["state"] == "canceled": 
                done.append(s)
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



########### notes


### from a buy order

# {'account_id': '03199a0c-f4d8-4cc6-b713-ffc39fa3d304', 'average_price': None, 'cancel_url': 'https://nummus.robinhood.com/orders/b3450d84-6e04-4a01-a026-61ac7ca
# dc361/cancel/', 'created_at': '2020-09-19T17:43:01.024204-04:00', 'cumulative_quantity': '0.000000000000000000', 'currency_pair_id': '7b577ce3-489d-4269-9408-79
# 6a0d1abb3a', 'executions': [], 'id': 'b3450d84-6e04-4a01-a026-61ac7cadc361', 'last_transaction_at': None, 'price': '6.220000000000000000', 'quantity': '0.803900
# 000000000000', 'ref_id': '2cb3e5d3-5aeb-4920-9804-b1193eb4e2c4', 'rounded_executed_notional': '0.00', 'side': 'buy', 'state': 'unconfirmed', 'time_in_force': 'g
# tc', 'type': 'market', 'updated_at': '2020-09-19T17:43:01.194170-04:00'}

### from a sell order

# {'account_id': '03199a0c-f4d8-4cc6-b713-ffc39fa3d304', 'average_price': None, 'cancel_url': 'https://nummus.robinhood.com/orders/100a69d3-db51-4f0d-af29-6eade42
# 4271f/cancel/', 'created_at': '2020-09-19T17:43:08.168510-04:00', 'cumulative_quantity': '0.000000000000000000', 'currency_pair_id': '3d961844-d360-45fc-989b-f6
# fca761d511', 'executions': [], 'id': '100a69d3-db51-4f0d-af29-6eade424271f', 'last_transaction_at': None, 'price': '11048.370000000000000000', 'quantity': '0.00
# 0475000000000000', 'ref_id': '4b390e26-610f-462b-b2d1-c36c0deb460a', 'rounded_executed_notional': '0.00', 'side': 'sell', 'state': 'unconfirmed', 'time_in_force
# ': 'gtc', 'type': 'market', 'updated_at': '2020-09-19T17:43:08.168543-04:00'}




####### printing the check order after initial send order

 
# Selling ETC if sufficient quantity, otherwise buy...
# 
# Not enough stock to sell, buying more instead...
# Buying $5 worth of ETC...
# {'account_id': '03199a0c-f4d8-4cc6-b713-ffc39fa3d304', 'average_price': None, 'cancel_url': 'https://nummus.robinhood.com/orders/3cb0a3f8-ecc6-4e19-b6f5-1853d17
# e9493/cancel/', 'created_at': '2020-09-19T17:50:07.049056-04:00', 'cumulative_quantity': '0.000000000000000000', 'currency_pair_id': '7b577ce3-489d-4269-9408-79
# 6a0d1abb3a', 'executions': [], 'id': '3cb0a3f8-ecc6-4e19-b6f5-1853d17e9493', 'last_transaction_at': None, 'price': '6.210000000000000000', 'quantity': '0.805200
# 000000000000', 'ref_id': 'b640e66d-a441-44cc-ae3d-7e5a27de4a2a', 'rounded_executed_notional': '0.00', 'side': 'buy', 'state': 'unconfirmed', 'time_in_force': 'g
# tc', 'type': 'market', 'updated_at': '2020-09-19T17:50:07.203329-04:00'}
# {'account_id': '03199a0c-f4d8-4cc6-b713-ffc39fa3d304', 'average_price': None, 'cancel_url': 'https://nummus.robinhood.com/orders/3cb0a3f8-ecc6-4e19-b6f5-1853d17
# e9493/cancel/', 'created_at': '2020-09-19T17:50:07.049056-04:00', 'cumulative_quantity': '0.000000000000000000', 'currency_pair_id': '7b577ce3-489d-4269-9408-79
# 6a0d1abb3a', 'executions': [], 'id': '3cb0a3f8-ecc6-4e19-b6f5-1853d17e9493', 'last_transaction_at': None, 'price': '6.210000000000000000', 'quantity': '0.805200
# 000000000000', 'ref_id': 'b640e66d-a441-44cc-ae3d-7e5a27de4a2a', 'rounded_executed_notional': '0.00', 'side': 'buy', 'state': 'unconfirmed', 'time_in_force': 'g
# tc', 'type': 'market', 'updated_at': '2020-09-19T17:50:07.203329-04:00'}
# ETH stock sellable: 0.0
# BTC stock sellable: 0.00189095
# 
# Selling BTC if sufficient quantity, otherwise buy...
# 
# Selling 5.25 of BTC...
# {'account_id': '03199a0c-f4d8-4cc6-b713-ffc39fa3d304', 'average_price': None, 'cancel_url': 'https://nummus.robinhood.com/orders/4e140a03-cdca-422e-8530-766b5d4
# 2654c/cancel/', 'created_at': '2020-09-19T17:50:14.195905-04:00', 'cumulative_quantity': '0.000000000000000000', 'currency_pair_id': '3d961844-d360-45fc-989b-f6
# fca761d511', 'executions': [], 'id': '4e140a03-cdca-422e-8530-766b5d42654c', 'last_transaction_at': None, 'price': '11044.720000000000000000', 'quantity': '0.00
# 0475000000000000', 'ref_id': '88decfe2-093f-471f-8118-cd3c41ce35ad', 'rounded_executed_notional': '0.00', 'side': 'sell', 'state': 'unconfirmed', 'time_in_force
# ': 'gtc', 'type': 'market', 'updated_at': '2020-09-19T17:50:14.195924-04:00'}
# {'account_id': '03199a0c-f4d8-4cc6-b713-ffc39fa3d304', 'average_price': '11044.724019000000000000', 'cancel_url': None, 'created_at': '2020-09-19T17:50:14.19590
# 5-04:00', 'cumulative_quantity': '0.000475000000000000', 'currency_pair_id': '3d961844-d360-45fc-989b-f6fca761d511', 'executions': [{'effective_price': '11044.7
# 24019000000000000', 'id': '4c73da17-fb9e-42a9-9e24-c322e57a3f24', 'quantity': '0.000475000000000000', 'timestamp': '2020-09-19T17:50:14.284000-04:00'}], 'id': '
# 4e140a03-cdca-422e-8530-766b5d42654c', 'last_transaction_at': '2020-09-19T17:50:14.284000-04:00', 'price': '11044.720000000000000000', 'quantity': '0.0004750000
# 00000000', 'ref_id': '88decfe2-093f-471f-8118-cd3c41ce35ad', 'rounded_executed_notional': '5.24', 'side': 'sell', 'state': 'filled', 'time_in_force': 'gtc', 'ty
# pe': 'market', 'updated_at': '2020-09-19T17:50:14.739274-04:00'}
# Sell order filled :)
