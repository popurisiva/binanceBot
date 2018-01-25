#!/usr/bin/env python

from binance.client import Client
from slackclient import SlackClient
import time
import json
import logging
from datetime import datetime
from decimal import Decimal

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
volumePercent = config.get('volumePercent', 4)
buyDifference = config.get('buyDifference', 0)
extCoinBalance = config.get('extCoinBalance', 0)
checkInterval = config.get('checkInterval', 30)
initialsell_price = config.get('initialsell_price', 0)
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


def determine_initial_buy_price(current_ticker):
    price = round(current_ticker - (current_ticker * round(Decimal(buyValuePercent), 2)), 8)
    return price


def determine_initial_sell_price(current_ticker):
    price = round(current_ticker + (current_ticker * round(Decimal(sellValuePercent), 2)), 8)
    return price


def get_oid(data):
    return data['clientOrderId']


def get_last_buy_order(completed_buy_orders):
    data = completed_buy_orders['datas']
    order_time = (data[0]['createdAt'])
    return order_time


def get_last_sell_order(completed_sell_orders):
    data = completed_sell_orders['datas']
    order_time = (data[0]['createdAt'])
    return order_time


def post_slack(order_type):
    net_profit_loss_percent = get_net_profit_or_loss()
    if net_profit_loss_percent:
        log("PROFIT/LOSS Percentage : " + str(net_profit_loss_percent))
    if token:
        log("Attempting to send message...")
        sc = SlackClient(token)
        text = order_type + " completed for " + currency
        if net_profit_loss_percent:
            text += " With a net gain of {0}".format(str(net_profit_loss_percent))
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=text
        )


def get_order_price(order_data):
    data = order_data['datas']
    data = data[0]
    price = data['dealPrice']
    return price


def is_within_check_time(time_to_check_in_millis, base_time_in_millis, interval_in_sec):
    return abs(time_to_check_in_millis - base_time_in_millis) <= (interval_in_sec * 1000)


def get_ticker_price():
    ticker = client.get_ticker(symbol=tokenPair)
    price = round(Decimal(ticker['lastPrice']), 8)
    return price


def place_order_pair():
    balance = client.get_asset_balance(currency)
    balance = (float(balance['free']) + float(extCoinBalance))
    buy_amount = determine_buy_amount(balance)
    price = get_ticker_price()
    buy_price = determine_initial_buy_price(price)
    log("setting buy of " + str(buy_amount) + " at " + str(buy_price))
    client.create_order(symbol=tokenPair, price=buy_price, quantity=buy_amount,
                        side='BUY', type='LIMIT', timeInForce='GTC', icebergQty=int(buy_amount/4))
    log('BUY order placed.')
    sell_amount = determine_sell_amount(balance)
    sell_price = determine_initial_sell_price(price)
    log("setting sell of " + str(sell_amount) + " at " + str(sell_price))
    client.create_order(symbol=tokenPair, price=sell_price, quantity=sell_amount,
                            side='SELL', type='LIMIT', timeInForce='GTC', icebergQty=int(sell_amount/4))
    log("SELL order placed.")


def get_net_profit_or_loss():
    buy_total = 0.0
    buy_qty_total = 0.0
    sell_total = 0.0
    sell_qty_total = 0.0
    change_percent = None
    #trades = client.get_my_trades(symbol=tokenPair)
    all_orders = client.get_all_orders(symbol=tokenPair)
    filled_orders = [order for order in all_orders if order['status'] == 'FILLED']
    for trade_item in filled_orders:
        # buy trade
        # if trade_item['side'] == 'BUY':
        #     buy_total += float(round(Decimal(trade_item['price']) * Decimal(trade_item['executedQty']), 8))
        #     buy_qty_total += float(round(Decimal(trade_item['executedQty']), 8))
        # # sell trade
        if trade_item['side'] == 'SELL':
            sell_total += float(round(Decimal(trade_item['price']) * Decimal(trade_item['executedQty']), 8))
            sell_qty_total += float(round(Decimal(trade_item['executedQty']), 8))
    # get available asset balance
    #current_balance = client.get_asset_balance(currency)
    ticker_price = get_ticker_price()
    if sell_total:
        avg_sell_price = round(Decimal(sell_total / sell_qty_total), 8)
    #buy_total += float(round(Decimal(current_balance['free']) + Decimal(current_balance['locked']), 8) * ticker_price)
    if avg_sell_price and ticker_price:
        change_percent = float(round((ticker_price - avg_sell_price)/ticker_price * 100, 2))
    return change_percent


def main():
    cycle = 0
    while True:
        try:
            buy_order_data = None
            sell_order_data = None
            open_orders = client.get_open_orders(symbol=tokenPair)
            try:
                if open_orders and open_orders[0]:
                    if open_orders[0]['side'] == 'SELL':
                        sell_order_data = open_orders[0]
                    else:
                        buy_order_data = open_orders[0]
                if open_orders and open_orders[1]:
                    if open_orders[1]['side'] == 'BUY':
                        buy_order_data = open_orders[1]
                    else:
                        sell_order_data = open_orders[1]
            except IndexError:
                # ignore
                pass
            if buy_order_data and sell_order_data:
                log(open_orders)
                log('The order pair still set!!!')
            elif (buy_order_data and not sell_order_data) or (sell_order_data and not buy_order_data):
                target_order_to_cancel = buy_order_data or sell_order_data
                try:
                    oid = get_oid(target_order_to_cancel)
                    log("Cancel order " + oid)
                    log(client.cancel_order(symbol=tokenPair, origClientOrderId=oid))
                except:
                    logging.info("Order cancellation failed!!!")
                post_slack(type)
                log('Order cancellation finished!!!')
                log('Placing a fresh set of order pair...')
                place_order_pair()
            else:
                log("No orders present...setting to ticker price")
                place_order_pair()

        except Exception as e:
            if e.code and e.code == -1013:
                log('The total amount does not met, need to increase limits....', logging.ERROR)
            log(e)

        if cycle == 100:
            log("Garbage collection")
            gc.collect()
        log("Waiting " + str(checkInterval) + " for next cycle...")
        time.sleep(int(checkInterval))

if __name__ == '__main__':
    main()
