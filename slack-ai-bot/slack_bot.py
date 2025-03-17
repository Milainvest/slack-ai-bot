import os
import subprocess
import asyncio
from typing import Optional, Dict, Any, List
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

# OpenHands agent tools
class OpenHandsTools:
    @staticmethod
    async def execute_bash(command: str, is_input: bool = False) -> Dict[str, Any]:
        """Execute a bash command and return the result"""
        try:
            if is_input:
                # 対話的なコマンドの処理（未実装）
                return {"error": "Interactive commands not supported yet"}
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "exit_code": process.returncode
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def str_replace_editor(command: str, path: str, old_str: Optional[str] = None,
                               new_str: Optional[str] = None, file_text: Optional[str] = None,
                               insert_line: Optional[int] = None) -> Dict[str, Any]:
        """Edit files using the str_replace_editor tool"""
        try:
            if command == "view":
                with open(path, 'r') as f:
                    content = f.read()
                return {"content": content}
            elif command == "create":
                if os.path.exists(path):
                    return {"error": f"File {path} already exists"}
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(file_text or "")
                return {"message": f"File created at {path}"}
            elif command == "str_replace":
                with open(path, 'r') as f:
                    content = f.read()
                if old_str not in content:
                    return {"error": f"Old string not found in {path}"}
                new_content = content.replace(old_str, new_str)
                with open(path, 'w') as f:
                    f.write(new_content)
                return {"message": f"File {path} updated"}
            else:
                return {"error": f"Command {command} not supported"}
        except Exception as e:
            return {"error": str(e)}

# OpenHands agent message handler
async def handle_openhands_message(message: str, channel_id: str) -> None:
    """Handle messages using OpenHands agent functionality"""
    try:
        # システムプロンプトを設定
        system_prompt = """あなたはOpenHands agentとして、以下の機能を提供します：
1. ファイルの表示・作成・編集
2. シェルコマンドの実行
3. GitHubとの連携

利用可能なツール：
- execute_bash: シェルコマンドを実行
- str_replace_editor: ファイルの操作

セキュリティ制限：
- 危険なコマンドは実行できません
- 特定のディレクトリ以外へのアクセスは制限されています
"""

        # OpenAIを使用して応答を生成
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        
        # 応答を解析
        ai_response = response.choices[0].message.content
        
        # コマンドの実行が必要な場合は実行
        if "```bash" in ai_response:
            # コマンドを抽出
            command = ai_response.split("```bash")[1].split("```")[0].strip()
            
            # コマンドを実行
            result = await OpenHandsTools.execute_bash(command)
            
            # 結果をSlackに送信
            if "error" in result:
                await send_slack_message(channel_id, f"エラーが発生しました：{result['error']}")
            else:
                output = result["stdout"] or result["stderr"]
                await send_slack_message(channel_id, f"コマンド実行結果：\n```\n{output}\n```")
        else:
            # 通常の応答を送信
            await send_slack_message(channel_id, ai_response)
            
    except Exception as e:
        await send_slack_message(channel_id, f"エラーが発生しました：{str(e)}")

# Slack message sender
async def send_slack_message(channel_id: str, text: str) -> None:
    """Send a message to Slack"""
    try:
        slack_client.chat_postMessage(
            channel=channel_id,
            text=text
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

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
                await send_slack_message(
                    channel_id,
                    f"メッセージを受信しました: {message}\n処理を開始します..."
                )
                
                # OpenHands agentとしてメッセージを処理
                await handle_openhands_message(message, channel_id)
                
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=54725)