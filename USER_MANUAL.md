# Openhands Slack Bot 使用マニュアル

このマニュアルでは、Openhandsボットの起動、使用方法、および終了の手順について説明します。

## 1. サーバーの起動方法

### 初回セットアップ

初めてボットを使用する場合は、以下の手順でセットアップを行います：

1. 必要なパッケージをインストールします：
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. `.env`ファイルを作成し、以下の環境変数を設定します：
   ```
   # Slackの設定
   SLACK_BOT_TOKEN=xoxb-your-token-here
   SLACK_SIGNING_SECRET=your-signing-secret-here
   
   # OpenAI APIの設定
   OPENAI_API_KEY=your-openai-api-key-here
   
   # サーバー設定
   PORT=54725
   HOST=0.0.0.0
   
   # 許可するディレクトリ（カンマ区切りで複数指定可能）
   ALLOWED_DIRS=.
   ```

3. Slackアプリの設定が完了していることを確認します（詳細は`SLACK_SETUP.md`を参照）。

### サーバーの起動

1. ターミナルで以下のコマンドを実行してボットサーバーを起動します：
   ```bash
   python3 slack_bot.py
   ```

2. 別のターミナルでngrokを起動して、外部からアクセス可能なURLを生成します：
   ```bash
   ngrok http 54725
   ```

3. ngrokが生成したURLを確認します：
   ```
   例：https://a1b2c3d4.ngrok.io
   ```

4. **初回のみ**：Slack APIの設定ページで、イベントサブスクリプションのRequest URLを以下のように設定します：
   ```
   https://あなたのngrokドメイン.ngrok.io/slack/events
   ```

5. サーバーのログにSlackからの接続確認リクエスト（challenge）が表示されることを確認します。

## 2. Openhandsとの会話方法

### 会話の始め方

1. Slackで、ボットを招待したチャンネルに移動します。

2. ボットにメッセージを送信します：
   ```
   こんにちは
   ```

3. ボットからの返信を待ちます。通常、以下のような応答があります：
   ```
   メッセージを受信しました: こんにちは
   処理を開始します...
   
   こんにちは！OpenHands agentとしてお手伝いします。シェルコマンドの実行やファイル操作など、どのようなことをお手伝いできますか？
   ```

### コマンドの実行

ボットにシェルコマンドを実行させる場合は、通常の会話でコマンドを伝えるだけです：

```
現在のディレクトリにあるファイルを表示して
```

ボットは、適切なコマンドを提案し、実行結果を返信します：

```
現在のディレクトリのファイルを表示します。以下のコマンドを実行します：

```bash
ls -la
```

コマンド実行結果：
total 40
drwxr-xr-x  7 user  staff   224 Mar 16 12:34 .
drwxr-xr-x  5 user  staff   160 Mar 15 10:20 ..
-rw-r--r--  1 user  staff  1234 Mar 16 12:30 README.md
-rw-r--r--  1 user  staff  5678 Mar 16 12:32 SLACK_SETUP.md
-rw-r--r--  1 user  staff   321 Mar 16 12:33 requirements.txt
-rw-r--r--  1 user  staff  9876 Mar 16 12:34 slack_bot.py
-rw-r--r--  1 user  staff   654 Mar 16 12:31 test_claude_integration.py
```

### ファイル操作

ファイルの表示や編集も同様に会話で指示できます：

```
slack_bot.pyファイルの内容を表示して
```

または

```
test.txtというファイルを作成して、その中に「これはテストファイルです」と書き込んでください
```

## 3. サーバーの停止と再起動

### サーバーの停止方法

1. サーバーを実行しているターミナルウィンドウで、`Ctrl+C`を押してサーバーを停止します。

2. ngrokを実行しているターミナルウィンドウでも、`Ctrl+C`を押してngrokを停止します。

### サーバーの再起動方法

サーバーを停止した後、再度起動する場合：

1. まず、ボットサーバーを起動します：
   ```bash
   python3 slack_bot.py
   ```

2. 別のターミナルでngrokを起動します：
   ```bash
   ngrok http 54725
   ```

3. **重要**: ngrokを再起動すると、URLが変更されます。新しいngrok URLをSlack APIの設定ページで更新する必要があります：
   ```
   https://新しいngrokドメイン.ngrok.io/slack/events
   ```

4. Slack APIの設定ページで「Save Changes」をクリックして、変更を保存します。

## 4. 会話履歴の管理

### 会話履歴のクリア

会話履歴をクリアしたい場合は、以下のAPIエンドポイントにPOSTリクエストを送信します：

```bash
curl -X POST https://あなたのngrokドメイン.ngrok.io/api/clear-history \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "C12345678"}'
```

`C12345678`の部分は、実際のSlackチャンネルIDに置き換えてください。

### システム状況の確認

ボットのシステム状況を確認するには、以下のAPIエンドポイントにGETリクエストを送信します：

```bash
curl https://あなたのngrokドメイン.ngrok.io/api/status
```

## 5. トラブルシューティング

### ボットが応答しない場合

1. サーバーのログを確認して、エラーメッセージがないか確認します。

2. ngrokのURLが変更されていないか確認し、Slack APIの設定ページで更新します。

3. 環境変数（特にSlackトークンとシークレット）が正しく設定されているか確認します。

4. ボットがSlackチャンネルに招待されているか確認します。

### エラーメッセージが表示される場合

1. 「Invalid request signature」エラーが表示される場合：
   - Slack署名シークレットが正しく設定されているか確認します。
   - ngrokのURLが正しくSlack APIの設定ページで設定されているか確認します。

2. OpenAI APIエラーが表示される場合：
   - OpenAI APIキーが正しく設定されているか確認します。
   - APIレート制限に達していないか確認します。

### その他の問題

他の問題が発生した場合は、サーバーログを確認し、必要に応じてデバッグレベルを調整します：

```python
# slack_bot.py内のロギングレベルを変更
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGからINFOに変更してログ量を減らす
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 6. 注意事項

- ngrokの無料版は2時間後に自動的に切断されます。長時間使用する場合は、定期的に再起動するか、有料版を検討してください。
- 本番環境では、ngrokの代わりに固定URLのサービス（Heroku、AWS、GCPなど）の使用を検討してください。
- ファイル操作やコマンド実行には適切なセキュリティ対策を行ってください。
- `ALLOWED_DIRS`環境変数で許可するディレクトリを制限することで、セキュリティを強化できます。
