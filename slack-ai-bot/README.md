# Slack AI Bot

SlackからメッセージをAIアシスタントに送信し、応答を受け取るボットです。

## 機能

- Slackからのメッセージ受信
- AIアシスタントとの対話
- エラー通知

## セットアップ

1. 必要なパッケージのインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
`.env`ファイルを作成し、以下の変数を設定します：
```
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
```

3. サーバーの起動:
```bash
python slack_bot.py
```

## 使用方法

1. Slackでボットにメッセージを送信
2. ボットがメッセージを受信し、AIアシスタントに転送
3. AIアシスタントからの応答がSlackに返信されます

## エラー通知

エラーが発生した場合や、AIのレート制限により処理が中断された場合、Slackチャンネルに通知が送信されます。