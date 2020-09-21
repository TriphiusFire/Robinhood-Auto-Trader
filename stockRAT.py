import robin_stocks as r
import json
import time
from os.path import isfile 

############ JSON FILES ##################

stock_file = "./rh_stock_data.json"    # stock symbols / LTP's 
preferences_file="./preferences.json"  # customize trade levels and buy amount
credentials_file= "./credentials.json" # login and password

############ FUNCTIONS ###################
    
#this is the price a market buy would trigger at
def ask(symbol): #test: works
    return float(r.get_latest_price(symbol,'ask_price')[0])

#this is the price a market sell would trigger at
def bid(symbol): #test: works
    return float(r.get_latest_price(symbol,'bid_price')[0])
#test
# print('ASM bid: ',bid(test_symbol))

#buy x worth of stock, returns the trade id
def buy(symbol,dollars):
    print("Buying $"+str(dollars)+" worth of "+ symbol+"...")
    trade = r.order_buy_fractional_by_price(symbol, dollars,'gfd','ask_price',False)
#     print(trade) # comment out when done testing
    return trade['id']
    
#sell x*change worth of stock, returns the trade id
def sell(symbol,dollars):
    print("Selling "+str(dollars)+" of "+ symbol+"...")
    trade = r.order_sell_fractional_by_price(symbol, dollars,'gfd','bid_price',False)
#     print(trade) # comment out when done testing
    return trade['id']

def cancel(ident):
    cancel = r.cancel_stock_order(ident)
#     print(cancel)
    return cancel

def getOrder(ident):
    order = r.get_stock_order_info(ident)
    print("Order state: " + order["state"])
    return order
    

############ PROGRAM ###################
    
print("\nRobinhood Auto Trader - STOCKS\n RAT-S V1.")

realTrading = False

doReal = input("\nFor mock trading just press <enter> to see which stocks *would* be bought or sold right now.  \nFor real trading type <r> and <enter>: ")
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

if not isfile(stock_file):
    print("\nYou need a file called rh_stock_data.json in the RAT folder.")
    print("This file stores a dictionary containing your stock symbols and the last price you traded each at")
    print('\nJSON data looks like {"SYM1":1.11, "SYM2":50.49} where each "symbol":price pair is comma separated with no comma after the last pair and with all pairs inside curly brackets {...}')
    ans = input("Press <Enter> when you have created rh_stock_data.json in the RHAST folder")

print("\nrh_stock_data.json in the RAT folder looks like...\n")
with open(stock_file) as json_data:
    d = json.load(json_data)
    print(json.dumps(d, indent=1))
input("\nYour stocks and the last trade prices of each on your account?\n\n<enter> if everything looks correct.\n")

numSymbols = len(d)
# print(numSymbols)



positions = r.get_open_stock_positions()

numPositions = len(positions)
quantities = {}

for i in range(0,numPositions):
#     print(positions[i])
#     print(json.dumps(positions[i],indent=1))
    quantities[r.get_instrument_by_url(positions[i]["instrument"])["symbol"]]=float(positions[i]["quantity"])
    

index = 0
check = {}
#s is symbol, d is the whole rh_stock_data json dictionary
for s in d:
    if s in quantities:
        print("\n"+s+" stock sellable: "+str(quantities[s]))
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
                with open(stock_file,'w') as outfile:
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
                        with open(stock_file,'w') as outfile:
                            json.dump(d,outfile)  
                    else: 
                        if getOrder(orderid)["state"]=="queued": cancel(orderid)
                        check[s]=orderid
                else: mockSell+=xSell
            else:
                print("Not enough stock to sell, buying more instead...")
                if realTrading:
                    orderid = buy(s,xBuy)
                    time.sleep(5)
                    if getOrder(orderid)["state"] == "filled":
                        d[s]=Ltp*change
                        print("re-up Buy order filled")
                        with open(stock_file,'w') as outfile:
                            json.dump(d,outfile)  
                    else: 
                        if getOrder(orderid)["state"]=="queued": cancel(orderid)
                        check[s]=orderid
                else: mockSpend+=xBuy
                        
    
# all the orders that were not filled 5 seconds later
# need to check for filled before saving new LTP
if realTrading:
    while len(check) > 0:
        print("Still not filled: LTP not updated so you may cancel these manually. Once all filled or cancelled this loop ends.  Trying again in 15 seconds...")
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
                with open(stock_file,'w') as outfile:
                            json.dump(d,outfile) 
                done.append(s)
            if order["state"] == "cancelled" or order["state"] == "canceled": 
                done.append(s)
        if len(done) > 0:
            for d in done:
                del check[d]
        
        time.sleep(15)
        print(check)
else:
    print("\nSpend amount would be: "+str(mockSpend))
    print("Sell amount would be: "+str(mockSell))
            
    
#keep window open till user hits <enter>
input()
        
    
    
    
    
    
######## TESTS ############

# trade = buy("ASM",1) #test: works
# print(trade)
# print(trade["id"]) # test: works
# cancel = r.cancel_stock_order('e2f3b028-900d-4583-b15e-bbf83adf7f11') # test: works
# print(cancel)
# trade = sell("ASM",1) #test: works
# cancel = r.cancel_stock_order('f5e182ad-8400-4b02-b569-6a09f7d05433')
# print(cancel)
# print(getOrder('fa2aed26-6e70-44ef-8a12-2f681056b0a7'))
# print(getOrder('fa2aed26-6e70-44ef-8a12-2f681056b0a7')['state'])
# cancel('fa2aed26-6e70-44ef-8a12-2f681056b0a7') # test: works

#### if you cancel the first time, print(cancel) shows only {}
#### but if you try to cancel an already cancelled order...
# Order f5e182ad-8400-4b02-b569-6a09f7d05433 cancelled
# {'detail': 'Order cannot be cancelled at this time.'}



###### what a sell return structure looks like... 

# {'id': 'f5e182ad-8400-4b02-b569-6a09f7d05433', 'ref_id': '17afa802-d009-4644-8780-fb3b5b5121d8', 'url': 'https://api.robinhood.com/orders/f5e182ad-8400-4b02-b56
# 9-6a09f7d05433/', 'account': 'https://api.robinhood.com/accounts/453164410/', 'position': 'https://api.robinhood.com/positions/453164410/b507e255-8116-4dd7-be84
# -38781e3e929a/', 'cancel': 'https://api.robinhood.com/orders/f5e182ad-8400-4b02-b569-6a09f7d05433/cancel/', 'instrument': 'https://api.robinhood.com/instruments
# /b507e255-8116-4dd7-be84-38781e3e929a/', 'cumulative_quantity': '0.00000000', 'average_price': None, 'fees': '0.00', 'state': 'unconfirmed', 'type': 'market', '
# side': 'sell', 'time_in_force': 'gfd', 'trigger': 'immediate', 'price': '0.91000000', 'stop_price': None, 'quantity': '1.10000000', 'reject_reason': None, 'crea
# ted_at': '2020-09-19T07:06:08.162760Z', 'updated_at': '2020-09-19T07:06:08.162772Z', 'last_transaction_at': '2020-09-19T07:06:08.162760Z', 'executions': [], 'ex
# tended_hours': False, 'override_dtbp_checks': False, 'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None, 'last_trail_price
# ': None, 'last_trail_price_updated_at': None, 'dollar_based_amount': None, 'total_notional': {'amount': '1.00', 'currency_code': 'USD', 'currency_id': '1072fc76
# -1862-41ab-82c2-485837590762'}, 'executed_notional': None, 'investment_schedule_id': None}
    
#     print("TEST floats: BID + ASK: "+str(ask(i)+bid(i)))

# print(json.dumps(json.loads(r.load_phoenix_account())))

# print(r.find_stock_orders(symbol='ASM',cancel=None,quantity=1))

# #return the average price of the most recent trade
# def getLTP(symbol):
#     get_stock_quote_


# portfolio_symbols = get_portfolio_symbols()
# print("Current Portfolio: " + str(portfolio_symbols) + "\n")
