Questions feel free to ask

# binance bot
This is an experimental bot for swing trading against the binance exchange. Set an upper and lower percentage that will place buy / sell orders. When an order triggers, the bracket will shift basing off the last order.

**This bot is designed to trade coins you currently have! At current, it does not support trying to trade on a currency of which you have a 0 balance.**

**Example: if you try to execute it on ZEC but have no ZEC coins, it will not work**

# DISCLAIMER

### I am not responsible for anything done with this bot. You use it at your own risk. There are no warranties or guarantees expressed or implied. You assume all responsibility and liability.

## Configuration

#### Note: An api key will need to be created with "Trade Limit" permissions

| Config Parameter  |  Type |  Default | Required  |  Description |
|---|---|---|---|---|
| apiKey  |  String |  none | Yes  |  API key for account access |
| apiSecret  | String  |  none |  Yes |  Secret key for account access |
| trade  | String  |  none | Yes | Base token used for exchange (example: BTC)  |
| currency | String  | none  |  Yes | Token to be traded (example: STRAT) |
| sellValuePercent  | Integer/Float  | 4  |  No | Difference in sell price of the previous successful order or market (on startup)  | 
| buyValuePercent  |  Integer/FLoat |  4 |  No | Difference in buy price of the previous successful order or market (on startup)   | 
| volumePercent  | Integer/Float  | 4  | No  |  Percent of your tokens to be placed leveraged | 
| buyDifference  |  Integer/Float |  0 |  No |  Percent adjustment to buy orders. Positive values buy more than sells. Negative values buys less than sell | 
| extCoinBalance | Integer/Float | 0| No | Off exchange balance|
| checkInterval | Integer | 30| No | How often the bot checks state|
| slackToken | string | empty | Yes | token for sending to slack |
| slackChannel | string | empty | Yes | channel for trade notificaiton | 


The percentage values are actual percentages...not decimals. So if you want to trade 3.25% you would input 3.25 in that value. I would also not recommend going below 10 seconds for the checkInterval. Otherwise, it's possible to induce a race condition with bittrex.

## buyDifference explanation

Setting the 'volumePercent' param with a 'buyDifference' of zero places matching buys / sells. Adjusting the 'buyDifference' changes only the buying behavior. It's been much more predictable and less prone to erroneous buys / sells.

To be transparent, here's the forumla being used to calculate the buy amount:

(balance + externalCoinBalance) * volumePercent * (1/(1 - volumePercent) * 1 + buyDifference)

NOTE: I've had the best experience with higher percentages for the sell / buy Values. I currently run 6 on both


#### Example file 

```json
{
  "apiKey": "yourapikey",
  "apiSecret": "yourapisecret",
  "trade": "BTC",
  "currency": "ELF",
  "sellValuePercent": 6,
  "buyValuePercent": 6,
  "volumePercent": 3,
  "buyDifference": 2,
  "extCoinBalance": 0,
  "checkInterval": 30,
  "slackToken": "",
  "slackChannel": ""
}
```
__the config file MUST be named botConfig.json__

## Usage
The bot is designed to trade a single token at a time. It's recommended to run it in the docker container.
Docker will need to be installed prior to trying to run this. To install Docker, see their installation guide:
https://docs.docker.com/engine/installation/
The docker image can be found at __popurisiva/binancebot__

To run:
docker run -d --name <name> -v /path/to/directory_containing_config_file:/config popurisiva/binancebot:latest

Example:
docker run -d --name elf -v /opt/botdefs/elf:/config --restart always popurisiva/binancebot:latest

-- The elf directory, in this case, contains the botConfig.json

## Utilities
Bots run without your intervention. It is recommended that you have a means to track your trades ergo, track the trades the bot is making for you. That is the same for this bot as well as any other bots you may try.

I highly recommend using the slack notification feature here.

## License
Code released under the [MIT License](https://github.com/popurisiva/binanceBot/master/LICENSE).
