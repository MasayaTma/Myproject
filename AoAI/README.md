#　プロジェクト名
AzureOpenAIお試しソリューション

##　概要
このプロジェクトはAzureOpenAIを使用したRAGの作成における初期のものです。
APIの接続などを行ったものなのでこれから先改良の余地は多々あると思うのでぜひカスタマイズしてみてください。
dev
ウィキペディアのスティービーワンダーのページの情報をもとに回答を生成するモデル。

dev2
AzureOpenAIのGPT4を使用してプロンプトをもとに回答を生成するウェブアプリ。

dev3
dev2に会話履歴やフィードバック機能やcsvのエクスポート機能を付与したもの（開発途中のためUiのみの変更となっております）。

dev4
Microsoftの公式ドキュメントから情報を取得し回答を生成するウェブアプリ。

dev5
BingAPIを使用しウェブ検索結果から質問に対する回答を生成するウェブアプリ。

## インストール方法
以下の手順に従ってプロジェクトをセットアップしてください。

1. リポジトリをクローンします。
   ```bash
   git clone https://github.com/MasayaTma/Myproject.git
   cd Myproject/AoAI
2. 仮想環境を作成します。
   ```python -m venv venv
   source venv/bin/activate  # Windowsの場合は `venv\Scripts\activate`
3. 依存関係をインストールします。
   ```pip install -r requirements.txt
4. 環境変数を設定します。
   ```AZURE_API_KEY=your_azure_api_key
   AZURE_ENDPOINT=your_azure_endpoint
   AZURE_API_VERSION=your_azure_api_version
   AZURE_DEPLOYMENT=your_azure_deployment
   BING_SUBSCRIPTION_KEY=your_azure_bing_subscription_key
5. Pythonファイルを実行します。

## 依存関係
langchain: 自然言語処理のためのライブラリ
gradio: インタラクティブなウェブアプリケーションを作成するためのライブラリ
yfinance: Yahoo Financeから株価データを取得するためのライブラリ
その他の依存関係はrequirements.txtを参照してください。

## トラブルシューティング
仮想環境の作成に失敗する: Pythonが正しくインストールされているか確認してください。
依存関係のインストールに失敗する: pipのバージョンを最新に更新してください。

##　貢献
1. フォークします。
2. 新しいブランチを作成します。
   ```git checkout -b feature/新機能
3. 変更をコミットします。
   ```git commit -m 'Add 新機能'
4. プルリクエストを作成します。

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。