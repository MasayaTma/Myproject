import dash
import dash as dcc
import dash as html
import plotly.express as px
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from pandas_datareader import data as web
import pandas_datareader as pdr
import yfinance as yf
import seaborn as sns
import datetime
import chardet

sns.set(font=['Yu Gothic'])

# データ読み込み
with open('portfolio.csv', 'rb') as f:
    result = chardet.detect(f.read())
df_pf = pd.read_csv('portfolio.csv', encoding=result['encoding'])
print(df_pf.columns)  # 列名の確認
print(df_pf)  # データの確認

# 総額の算出
df_pf['取得総額(円)'] = df_pf['取得単価(円)'] * df_pf['取得数']
df_pf

new_price_list = []
for i in range(len(df_pf)):
    s_code = str(int(df_pf.iloc[i]['証券コード'])) + ".T"  # 証券コードに.Tを追加
    get_price = df_pf.iloc[i]['取得単価(円)']
    get_num = int(df_pf.iloc[i]['取得数'])
    ticker_info = yf.Ticker(s_code)
    new_price = ticker_info.history(period="max")["Open"]
    new_price = new_price.tail(1).values
    new_price_list.append(new_price)
new_price_list

np_sum = np.concatenate(new_price_list)

df_new = pd.DataFrame(np_sum, index=df_pf.index, columns=['最新価格(円)'])
df_new
df_new = pd.concat([df_pf, df_new], axis=1)
df_new

# 重複インデックスの削除
df_new = df_new[~df_new.index.duplicated(keep='first')]

# 最新の価格での総額算出
df_new['最新総額(円)'] = df_new['最新価格(円)'] * df_pf['取得数']
df_new

# 評価損益
df_new['評価損益(円)'] = df_new['最新総額(円)'] - df_new['取得総額(円)']
df_new

# 全体資産の可視化
title_name = '取得総額(円)'
plt.title(title_name)
plt.pie(df_new[title_name], labels=df_new['銘柄名'], autopct='%1.1f%%', counterclock=False, startangle=90)
plt.axis('equal')
plt.show()

title_name = '最新総額(円)'
plt.title(title_name)
plt.pie(df_new[title_name], labels=df_new['銘柄名'], autopct='%1.1f%%', counterclock=False, startangle=90)
plt.axis('equal')
plt.show()

# 評価損益の可視化
title_name = '評価損益(円)'
plt.title(title_name)
plt.bar(df_new['銘柄名'], df_new[title_name])
plt.show()
