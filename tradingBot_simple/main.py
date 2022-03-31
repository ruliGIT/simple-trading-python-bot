'''
import pandas_datareader as web

stocks = []
f = open("symbols.txt", "r")
for line in f:
    stocks.append(line.strip())

f.close()

web.DataReader(stocks, "yahoo", start="2000-1-1", end="2019-12-31")["Adj Close"].to_csv("prices.csv")
web.DataReader(stocks, "yahoo", start="2000-1-1", end="2019-12-31")["Volume"].to_csv("volume.csv")
'''

import pandas as pd
import numpy as np
import datetime as dt
import math
import warnings
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

prices = pd.read_csv("prices.csv", index_col="Date", parse_dates=True)
volume_changes = pd.read_csv("volume.csv", index_col="Date", parse_dates=True).pct_change()*100

today = dt.date(2000, 1, 15)
sim_end = dt.date(2019, 12, 31)
tickers = []
transaction_id = 0
money = 1000000
portfolio = {}
active_log = []
transaction_log = []

# Extracting the current stock price

def get_price(date, ticker):
    global prices
    return prices.loc[date][ticker]

# Transaction function: If a stock is being bought, a log of this transaction is added 
# to both activelog and transactionlog arrays. 
# If a stock is being sold then it’s log will be deleted from actionlog 
# but still added to a transactionlog.

def transaction(id, ticker, amount, price, type, info):
    global transaction_id
    if type == "buy":
        exp_date = today + dt.timedelta(days=14)
        transaction_id += 1
    else:
        exp_date = today
    if type == "sell":
        data = {
            "id": id, 
            "ticker": ticker, 
            "amount": amount, 
            "price": price,
            "date": today,
            "type": type,
            "exp_date": exp_date,
            "info": info
        }
    elif type == "buy":
        data = {
            "id": transaction_id, 
            "ticker": ticker, 
            "amount": amount, 
            "price": price,
            "date": today,
            "type": type,
            "exp_date": exp_date,
            "info": info
        }
        active_log.append(data)
    transaction_log.append(data)

# Buy function: For every item in our “shopping list”, 
# the function will find the price of the stock. 
# If this is a number (is not a NaN value) then it will find the actual amount of money
# that will be spent, subtract this from the money variable and add the number of stocks we bought to our portfolio. 

def buy(interest_list, allocated_money):
    global money, portfolio
    for item in interest_list:
        price = get_price(today.isoformat(), item)
        if not np.isnan(price):
            quantity = math.floor(allocated_money/price)
            money -= quantity*price
            portfolio[item] += quantity
            transaction(0, item, quantity, price, "buy", "")

# Sell function:

def sell():
    global money, portfolio, prices, today
    items_to_remove = []
    for i in range(len(active_log)):
        log = active_log[i]
        if log["exp_date"] <= today and log["type"] == "buy":
            tick_price = get_price(today.isoformat(), log["ticker"])
            if not np.isnan(tick_price):
                money += log["amount"]*tick_price
                portfolio[log["ticker"]] -= log["amount"]
                transaction(log["id"], log["ticker"], log["amount"], tick_price, "sell", log["info"])
                items_to_remove.append(i)
            else:
                log["exp_date"] += dt.timedelta(day=1)
    items_to_remove.reverse()
    for elem in items_to_remove:
        active_log.remove(active_log[elem])

# Simulation iteration

def simulation():
    global today, volume_changes, money
    start_date = today - dt.timedelta(days=14)
    series = volume_changes.loc[start_date:today].mean()
    interest_list = series[series > 100].index.tolist()
    sell()
    if len(interest_list) > 0:
        money_to_allocate = 500000 / len(interest_list)
        buy(interest_list, money_to_allocate)

# Helper functions

def get_indices():
    global tickers
    f = open("symbols.txt", "r")
    for line in f:
        tickers.append(line.strip())
    f.close()

def trading_day():
    global prices, today
    return np.datetime64(today) in list(prices.index.values)

def current_value():
    global money, portfolio, today, prices
    value = money
    for ticker in tickers:
        tick_price = get_price(today.isoformat(), ticker)
        if not np.isnan(tick_price):
            value += portfolio[ticker] * tick_price
    return int(value*100)/100

def main():
    global today
    get_indices()
    x = []
    y = []
    for ticker in tickers:
        portfolio[ticker] = 0
    while today < sim_end:
        while not trading_day():
            today += dt.timedelta(days=1)
        simulation()
        current_p_value = current_value()

        #plot
        x.append(today)
        y.append(current_p_value)
        
        print(current_p_value, today)
        today += dt.timedelta(days=7)
        
    plt.plot(x,y)
    plt.show()

main()