# プロジェクト名
Web Scraping

## 概要
Pythonを使用したウェブスクレイピングを気軽に試すことができるサンプルコードです。
一部AzureOpenAIを組み合わせたものがあります。
また内容を変更してサイトのクロールをする際は自己責任でお願いします。

qiita-2.py:Qiitaからトレンドの記事を抜き出しExcelに書き込むソリューション
qiita-4.py:gradioUI状に記事のタイトルとAzureOpenAIによる内容の要約を表示するソリューション
github.py:githubから現在のトレンドコードのリンクを抜き出しcsvに書き込みます

## インストール方法
以下の手順に従ってプロジェクトをセットアップしてください。

1. リポジトリをクローンします。
   ```
   bash
   git clone https://github.com/MasayaTma/Myproject.git
   cd Myproject/Scraping
2. 仮想環境を作成します。
   ```
   python -m venv venv
   source venv/bin/activate  # Windowsの場合は `venv\Scripts\activate`
3. 依存関係をインストールします。
   ```
   pip install -r requirements.txt
4. 環境変数を設定します。（qiita-4.pyを実行する場合のみ）
   ```
   AZURE_API_KEY=your_azure_api_key
   AZURE_ENDPOINT=your_azure_endpoint
   AZURE_API_VERSION=your_azure_api_version
   AZURE_DEPLOYMENT=your_azure_deployment
5. Pythonファイルを実行します。

## トラブルシューティング
仮想環境の作成に失敗する: Pythonが正しくインストールされているか確認してください。
依存関係のインストールに失敗する: pipのバージョンを最新に更新してください。
スクレイピングがうまくできない: Googlechromeのウェブドライバーを同一ファイル内に格納する必要があります。また現在使用されているGooglechromeのバージョンと同一のドライバーが必要になります。
ファイルが格納されない: 同一ファイル内に"output"フォルダを参照し保存するためご準備ください。

## 貢献
1. フォークします。
2. 新しいブランチを作成します。
   ```
   git checkout -b feature/new-function
3. 変更をコミットします。
   ```
   git commit -m 'Add new-function'
4. プルリクエストを作成します。

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。