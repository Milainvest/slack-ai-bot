import os
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from slack_sdk.signature import SignatureVerifier

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
signature_verifier = SignatureVerifier(os.environ.get("SLACK_SIGNING_SECRET"))

# Slack Event Subscriptionsの検証用
@app.route("/slack/events", methods=["POST"])
def slack_events():
    # リクエストの署名を検証
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({"error": "Invalid request signature"}), 403

    # リクエストの検証
    if "challenge" in request.json:
        return jsonify({"challenge": request.json["challenge"]})

    # イベントの処理
    event_data = request.json
    if "event" in event_data:
        event = event_data["event"]
        
        # メッセージイベントの処理
        if event["type"] == "message" and "bot_id" not in event:
            try:
                channel_id = event["channel"]
                message = event["text"]
                
                # メッセージを受信したことを通知
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=f"メッセージを受信しました: {message}\n処理を開始します..."
                )
                
                # ここでAIとの対話処理を実装予定
                
            except SlackApiError as e:
                print(f"Error sending message: {e.response['error']}")
                
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=52987)