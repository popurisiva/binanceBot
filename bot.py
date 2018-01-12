#!/usr/bin/env python
__author__ = 'sivapopuri'

from binance.client import Client
from slackclient import SlackClient
import time
import json
import logging
from datetime import datetime

logger = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log(message, level=logging.INFO):
    logger.log(level, "[" + str(datetime.utcnow()) + "] " + str(message))

with open("config/botConfig.json", "r") as fin:
    config = json.load(fin)

apiKey = str(config['apiKey'])
apiSecret = str(config['apiSecret'])
trade = config['trade']
currency = config['currency']
sellValuePercent = config.get('sellValuePercent', 4)
buyValuePercent = config.get('buyValuePercent', 4)
volumePercent = config.get('buyVolumePercent', 4)
buyDifference = config.get('buyDifference', 0)
extCoinBalance = config.get('extCoinBalance', 0)
checkInterval = config.get('checkInterval', 30)
initialSellPrice = config.get('initialSellPrice', 0)
tradeAmount = config.get('tradeAmount', 0)
channel = config['slackChannel']
token = config['slackToken']

# global constants
client = Client(apiKey, apiSecret)
volumePercent *= .01
sellValuePercent *= .01
buyValuePercent *= .01
buyDifference *= .01
tokenPair = currency.upper() + trade.upper()

def determine_sell_amount(balance):
    return int(round(balance * volumePercent))

def determine_buy_amount(balance):
    amount = int(round(balance * volumePercent * (1 / (1 - volumePercent) * 1 + buyDifference)))
    return amount

def determine_initial_buy_price(currentTicker):
    price = round(currentTicker - (currentTicker * buyValuePercent), 8)
    return price

def determine_initial_sell_price(currentTicker):
    price = round(currentTicker + (currentTicker * sellValuePercent), 8)
    return price

def get_oid(data):
    return data['clientOrderId']


def get_last_buy_order(completedBuyOrders):
    data = completedBuyOrders['datas']
    orderTime = (data[0]['createdAt'])
    return(orderTime)

def get_last_sell_order(completedSellOrders):
    data = completedSellOrders['datas']
    orderTime = (data[0]['createdAt'])
    return (orderTime)

def post_slack(type):
    log("Attempting to send message...")
    sc = SlackClient(token)
    text = type + " completed for " + currency
    sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=text
    )

def get_order_price(orderData):
    data = orderData['datas']
    data = data[0]
    price = data['dealPrice']
    return price


def is_within_check_time(timeToCheckInMillis, baseTimeInMillis, intervalInSec):
    return abs(timeToCheckInMillis - baseTimeInMillis) <= (intervalInSec * 1000)


def place_order_pair():
    balance = client.get_asset_balance(currency)
    log('BALANCE' + str(balance))
    balance = (float(balance['free']) + float(extCoinBalance))
    buyAmount = determine_buy_amount(balance)
    ticker = client.get_ticker(symbol=tokenPair)
    price = float(ticker['lastPrice'])
    buyPrice = determine_initial_buy_price(price)
    log("setting buy of " + str(buyAmount) + " at " + str(buyPrice))
    log(client.create_order(symbol=tokenPair, price=buyPrice, quantity=buyAmount,
                            side='BUY', type='LIMIT', timeInForce='GTC', icebergQty=int(buyAmount/4)))
    sellAmount = determine_sell_amount(balance)
    sellPrice = determine_initial_sell_price(price)
    log("setting sell of " + str(sellAmount) + " at " + str(sellPrice))
    log(client.create_order(symbol=tokenPair, price=sellPrice, quantity=sellAmount,
                            side='SELL', type='LIMIT', timeInForce='GTC', icebergQty=int(sellAmount/4)))

cycle = 0
while True:
    try:
        buyOrderData = None
        sellOrderData = None
        openOrders = client.get_open_orders(symbol=tokenPair)
        try:
            if openOrders and openOrders[0]:
                if openOrders[0]['side'] == 'SELL':
                    sellOrderData = openOrders[0]
                else:
                    buyOrderData = openOrders[0]
            if openOrders and openOrders[1]:
                if openOrders[1]['side'] == 'BUY':
                    buyOrderData = openOrders[1]
                else:
                    sellOrderData = openOrders[1]
        except IndexError:
            # ignore
            pass
        if buyOrderData and sellOrderData:
            log(openOrders)
            log('The order pair still set!!!')
        elif (buyOrderData and not sellOrderData) or (sellOrderData and not buyOrderData):
            targetOrderToCancel = buyOrderData or sellOrderData
            try:
                oid = get_oid(targetOrderToCancel)
                log("Cancel order " + oid)
                log(client.cancel_order(symbol=tokenPair, origClientOrderId=oid))
            except, e:
                log(e, logging.ERROR)
                logging.info ("Order cancellation failed!!!")
                if token:
                    post_slack(type)
            log('Order cancellation finished!!!')
            log('Placing a fresh set of order pair...')
            place_order_pair()
        else:
            log("No orders present...setting to ticker price")
            place_order_pair()

    except Exception as e:
        if e.code == -1013:
            log('The total amount does not met, need to increase limits....', logging.ERROR)
        log(e)

    if cycle == 100:
        log("Garbage collection")
        gc.collect()
        count = 0
    log("Waiting " + str(checkInterval) + " for next cycle...")
    time.sleep(int(checkInterval))