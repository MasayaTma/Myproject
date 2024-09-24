import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import yfinance as yf
import seaborn as sns
from datetime import datetime, timedelta

sns.set(font=['Yu Gothic'])

# データ読み込み
df_pf = pd.read_csv('portfolio.csv', encoding='utf-8')  # 必要に応じてencodingを変更
print(df_pf.columns)  # 列名の確認
print(df_pf)  # データの確認

# 総額の算出
df_pf['取得総額(円)'] = df_pf['取得単価(円)'] * df_pf['取得数']
df_pf

# 過去1年分のデータ取得
def get_historical_prices(df):
    historical_data = {}
    for i in range(len(df)):
        s_code = str(int(df.iloc[i]['証券コード'])) + ".T"  # 証券コードに.Tを追加
        ticker_info = yf.Ticker(s_code)
        history = ticker_info.history(period="1y")  # 過去1年分のデータを取得
        history['銘柄名'] = df.iloc[i]['銘柄名']  # 銘柄名を追加
        historical_data[df.iloc[i]['銘柄名']] = history[['Close', '銘柄名']]  # 終値データのみを保存
    return historical_data

# 過去1年分の株価データ取得
historical_prices = get_historical_prices(df_pf)

# 各銘柄ごとのデータフレームを統合
df_history = pd.DataFrame()
for name, data in historical_prices.items():
    df_history = pd.concat([df_history, data])

# 最新価格と予測を行う関数
def forecast_prices(df, periods=30):
    forecast_data = {}
    for i in range(len(df)):
        s_code = str(int(df.iloc[i]['証券コード'])) + ".T"
        ticker_info = yf.Ticker(s_code)
        history = ticker_info.history(period="1y")['Close']
        
        # 移動平均線で予測 (単純な方法として)
        rolling_mean = history.rolling(window=5).mean().dropna()
        last_price = history.iloc[-1]  # ilocで最新の価格を取得
        
        # 単純な予測：最後の価格をベースに±移動平均の変化率を使って予測
        predictions = [last_price + (np.mean(rolling_mean[-5:]) - last_price) * (i/periods) for i in range(1, periods+1)]
        
        future_dates = [history.index[-1] + timedelta(days=i) for i in range(1, periods+1)]
        forecast_df = pd.DataFrame({'Date': future_dates, 'Forecast': predictions})
        forecast_df['銘柄名'] = df.iloc[i]['銘柄名']  # 銘柄名を追加
        forecast_data[df.iloc[i]['銘柄名']] = forecast_df
    return forecast_data

# 株価予測データ
forecast_data = forecast_prices(df_pf)

# Dashアプリの初期化
app = dash.Dash(__name__)

# レイアウトの設定
app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0),
    html.Div(id='live-update-text'),
    dcc.Graph(id='portfolio-performance'),
    dcc.Graph(id='forecast-performance')  # 新しい予測グラフ
])

# コールバック関数の設定
@app.callback(
    [Output('live-update-text', 'children'),
     Output('portfolio-performance', 'figure'),
     Output('forecast-performance', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_stock_price(n):
    # 最新の価格情報はすでに取得済みの historical_data から取得
    df_pf['最新価格(円)'] = [data['Close'].iloc[-1] for data in historical_prices.values()]
    
    # 総額の更新
    df_pf['最新総額(円)'] = df_pf['最新価格(円)'] * df_pf['取得数']
    df_pf['評価損益(円)'] = df_pf['最新総額(円)'] - df_pf['取得総額(円)']
    
    # 最新の株価情報を表示
    latest_prices = df_pf[['銘柄名', '最新価格(円)']].to_dict('records')
    price_text = [f"{record['銘柄名']}: {record['最新価格(円)']}円" for record in latest_prices]
    
    # ポートフォリオのパフォーマンスをグラフで表示
    fig_portfolio = px.line(df_history, x=df_history.index, y='Close', color='銘柄名', 
                            title='ポートフォリオの過去1年の推移')

    # 株価予測グラフ
    forecast_df = pd.concat([df for df in forecast_data.values()])
    
    # 縦軸の範囲を調整するために最小値と最大値を計算
    y_min = forecast_df['Forecast'].min() * 0.95  # 最小値の95%に設定
    y_max = forecast_df['Forecast'].max() * 1.05  # 最大値の105%に設定
    
    fig_forecast = px.line(forecast_df, x='Date', y='Forecast', color='銘柄名', 
                           title='銘柄ごとの1ヶ月の株価予測')

    # yaxis の範囲を設定
    fig_forecast.update_layout(
        yaxis=dict(range=[y_min, y_max])
    )
    
    return html.Ul([html.Li(text) for text in price_text]), fig_portfolio, fig_forecast

if __name__ == '__main__':
    app.run_server(debug=True)
