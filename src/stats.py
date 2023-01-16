import json
import os

import numpy as np
import pandas as pd
from yahoo_fin.stock_info import *

stocks = os.listdir("../stocks/")
print(len(stocks))

ticker_to_data = {}
for stock in stocks:
    with open(f"../stocks/{stock}", 'r') as f:
        data = json.load(f)
        ticker_to_data[stock[:-5]] = {k: data[k] for k in data.keys() if k != stock[:-5].replace('/', '-')}
        ticker_to_data[stock[:-5]]['description'] = data[stock[:-5].replace('-', '/')]

tickers = [ticker.replace('-', '/') for ticker in ticker_to_data.keys()]

print(get_dividends('aapl'))

clusters = pd.read_csv('../clusters.csv')
clusters = clusters.drop(columns=['Unnamed: 0'])

print(clusters[clusters['ticker'] == 'TTE'])
print(clusters[clusters['cluster'] == 2])

tte_cluster = clusters[clusters['cluster'] == 2]

print(ticker_to_data['TTE'])

tte_sector_buddies = {t: ticker_to_data[t] for t in ticker_to_data.keys() if 'sector' in ticker_to_data[t] and ticker_to_data[t]['sector'] == 'Energy'}
print(len(tte_sector_buddies))

count = 0
for t in tte_sector_buddies:
    if len(tte_cluster[tte_cluster['ticker'] == t]) == 0:
        count += 1
        print(t)

print(count)


quote_tables = {}
for t in tte_sector_buddies:
    try:
        quote_table = get_quote_table(t)
        print("------------------")
        print(t)
        print(quote_table)
        quote_tables[t] = quote_table
    except Exception as e:
        pass

with open('../tte-cluster-quote-tables', 'w') as f:
    json.dump(quote_tables, f)


with open('../tte-cluster-quote-tables', 'r') as f:
    tte_cluster_stats = json.load(f)

print(len(tte_cluster_stats))

sum_pe, sum_mkt_cap = 0, 0
market_caps = []
known_pe_ratios = {
    'XOM': 9.24,
    'CVX': 10.1,
    'SLB': 28.15
}
for t in tte_cluster_stats:
    data = tte_cluster_stats[t]

    if 'PE Ratio (TTM)' in data and 'Market Cap' in data:
        pe_ratio = float(data['PE Ratio (TTM)'])
        mkt_cap = data['Market Cap']
        print(t)
        print(data)

        if isinstance(mkt_cap, str):
            if mkt_cap[-1] == 'T':
                mkt_cap = float(mkt_cap[:-1]) * 10**12
            elif mkt_cap[-1] == 'B':
                mkt_cap = float(mkt_cap[:-1]) * 10**9
            elif mkt_cap[-1] == 'M':
                mkt_cap = float(mkt_cap[:-1]) * 10 ** 6
            else:
                print(t + ": " + mkt_cap)

        print(mkt_cap)
        print(pe_ratio)

        if pd.notna(mkt_cap):
            market_caps.append({'ticker': t, 'market cap': mkt_cap})
        else:
            continue

        if pd.notna(pe_ratio):
            sum_mkt_cap += mkt_cap
            sum_pe += float(pe_ratio) * mkt_cap
        elif t in known_pe_ratios:
            sum_mkt_cap += mkt_cap
            sum_pe += known_pe_ratios[t] * mkt_cap


avg_pe = sum_pe / sum_mkt_cap
print(f"Total market cap: {sum_mkt_cap}")
print(f"Average P/E (TTM): {avg_pe}")

print("Largest by market cap:")
print(sorted(market_caps, key=lambda x: x['market cap'], reverse=True))


