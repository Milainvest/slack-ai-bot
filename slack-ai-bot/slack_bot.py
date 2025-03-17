import os
from fastapi import FastAPI, Request, Response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from slack_sdk.signature import SignatureVerifier
import openai
import uvicorn
import json

# 環境変数の読み込み
load_dotenv()

app = FastAPI()
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
signature_verifier = SignatureVerifier(os.environ.get("SLACK_SIGNING_SECRET"))

# Slack Event Subscriptionsの検証用
@app.post("/slack/events")
async def slack_events(request: Request):
    # リクエストボディを取得
    body = await request.body()
    # ヘッダーを取得
    headers = request.headers
    
    # リクエストの署名を検証
    if not signature_verifier.is_valid_request(body, headers):
        return {"error": "Invalid request signature"}, 403

    # JSONデータを解析
    event_data = await request.json()
    
    # リクエストの検証
    if "challenge" in event_data:
        return {"challenge": event_data["challenge"]}

    # イベントの処理
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
                
                # OpenAIを使用して応答を生成
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは親切で丁寧なアシスタントです。"},
                        {"role": "user", "content": message}
                    ]
                )
                
                # 応答をSlackに送信
                ai_response = response.choices[0].message.content
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=ai_response
                )
                
            except SlackApiError as e:
                print(f"Error sending message: {e.response['error']}")
                
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=54725)