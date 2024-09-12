import yfinance as yf

# ソフトバンクグループの情報を取得（Tは東証を表す）
ticker_info = yf.Ticker("9984.T")

# 会社概要(info)を出力
ticker_info.info
# 株価データ（日毎）を取得
hist = ticker_info.history(period="max")
print(ticker_info.info)