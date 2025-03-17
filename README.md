# Slack AI Bot

SlackからメッセージをAIアシスタントに送信し、応答を受け取るボットです。

## 機能

- Slackからのメッセージ受信
- AIアシスタント（OpenHands）との対話
- シェルコマンドの実行
- ファイルの操作
- エラー通知
- 会話履歴の管理

## セットアップ

1. 必要なパッケージのインストール:
```bash
python3 -m pip install -r requirements.txt
```

2. 環境変数の設定:
`.env`ファイルを作成し、以下の変数を設定します：
```
# Slackの設定
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# OpenAI APIの設定（必要な場合）
OPENAI_API_KEY=your-openai-api-key-here

# サーバー設定
PORT=54725
HOST=0.0.0.0

# デバッグモード
DEBUG=True

# 許可するディレクトリ
ALLOWED_DIRS=.
```

3. サーバーの起動:
```bash
python3 slack_bot.py
```

4. ngrokを使用したトンネリング:
```bash
ngrok http 54725
```
これにより、外部からアクセス可能なURLが生成されます。Slackイベント購読のURLには`https://あなたのドメイン.ngrok.io/slack/events`を使用します。

5. Slackアプリケーションのセットアップ:
詳細なSlackアプリケーションの設定手順については、[SLACK_SETUP.md](./SLACK_SETUP.md)を参照してください。この手順に従って、Slackアプリケーションを作成し、必要なスコープと権限を設定し、イベント購読を設定します。

## 簡単起動方法

ボットを起動するには、2つのターミナルを開き、それぞれで以下のスクリプトを実行します：

**ターミナル1（ボットサーバー）**：
```bash
chmod +x start_bot.sh  # 初回のみ実行
./start_bot.sh
```

**ターミナル2（ngrokトンネル）**：
```bash
chmod +x start_ngrok.sh  # 初回のみ実行
./start_ngrok.sh
```

詳細な使用方法、トラブルシューティング、および会話の始め方と終了方法については、[USER_MANUAL.md](./USER_MANUAL.md)を参照してください。

## 使用方法

1. Slackでボットにメッセージを送信
2. ボットがメッセージを受信し、AIアシスタントに転送
3. AIアシスタントからの応答がSlackに返信されます

## エラー通知

エラーが発生した場合や、AIのレート制限により処理が中断された場合、Slackチャンネルに通知が送信されます。