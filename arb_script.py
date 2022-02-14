import ccxt
import pandas as pd

#Set up market instances
ftx = ccxt.ftx({'enableRateLimit' : 'True'})
binance = ccxt.binance({
	'enableRateLimit' : 'True',
	'options' : {'defaultType' : 'future'}
})

#Get a list of all futures market from the two exchanges
ftx_all_markets = list(ftx.load_markets())
ftx_markets = []
normalized_markets = []
for market in ftx_all_markets: #Get only futures markets
	if '-PERP' in market:
		ftx_markets.append(market)
		normalized_name = market.replace('-PERP', '')
		normalized_markets.append(normalized_name)

binance_markets = list(binance.load_markets())

#Create a list with normalized markets that are common to ftx & binance
common_markets = []
for market in normalized_markets: #Check if there is a common market in ftx and binance and append it to the list
	is_in_both_market = any(market in binance_market for binance_market in binance_markets)
	if is_in_both_market and market != 'DEFI':
		common_markets.append(market)

#fetch order books and get best bid and ask for each exchange
spread = {'spread' : [], 
		'market' : [], 
		'ftx_depth' : [],
		'binance_depth' : [],
		'arb_execution' : []}


for market in common_markets:
	try:
		ftx_order_book = ftx.fetch_order_book(market + '-PERP')
		binance_order_book = binance.fetch_order_book(market + '/USDT')
		ftx_ticker = {'bid' : ftx_order_book['bids'][0][0],
					'ask' : ftx_order_book['asks'][0][0]}

		binance_ticker = {'bid' : binance_order_book['bids'][0][0],
						'ask' : binance_order_book['asks'][0][0]}

		#Compute the spreads both ways
		spread1 = (binance_ticker['ask'] - ftx_ticker['bid']) / ftx_ticker['bid']
		spread2 = (ftx_ticker['ask'] - binance_ticker['bid']) / binance_ticker['bid']
		
		#Select the best spread and gather market depths & arbitrage to execute
		if max(spread1, spread2) == spread1:
			spread['spread'].append(spread1 * 100 - 0.17) #Spread minus trading fees (0.1% binance and 0.07% FTX)
			spread['market'].append(market)
			#Get market depth in $
			spread['ftx_depth'].append(ftx_order_book['bids'][0][1] * ftx_ticker['bid'])
			spread['binance_depth'].append(binance_order_book['asks'][0][1] * binance_ticker['ask'])
			spread['arb_execution'].append('long on binance & short on FTX')
		else:
			spread['spread'].append(spread2 * 100 - 0.17 * 2) #Spread minus trading fees (0.1% binance and 0.07% FTX)
			spread['market'].append(market)
			#Get market depth in $
			spread['ftx_depth'].append(ftx_order_book['asks'][0][1] * ftx_ticker['ask'])
			spread['binance_depth'].append(binance_order_book['bids'][0][1] * binance_ticker['bid'])
			spread['arb_execution'].append('short on binance & long on FTX')
	except:
		spread['spread'].append(0)
		spread['market'].append(market + 'Error')
		spread['ftx_depth'].append(0)
		spread['binance_depth'].append(0)
		spread['arb_execution'].append('Error')

spread = pd.DataFrame(spread)
spread = spread.sort_values(by=['spread'], ascending=False)
print(spread)

###COMPTER DEUX FOIS LES FEES