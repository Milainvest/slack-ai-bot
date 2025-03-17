import os
import subprocess
import asyncio
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from slack_sdk.signature import SignatureVerifier
import openai
import uvicorn
import json

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

# 環境変数の確認
slack_token = os.environ.get("SLACK_BOT_TOKEN")
signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
openai_api_key = os.environ.get("OPENAI_API_KEY")

if not slack_token or not signing_secret:
    logger.error("環境変数が設定されていません：SLACK_BOT_TOKEN または SLACK_SIGNING_SECRET")
    logger.info("環境変数を.envファイルに設定するか、直接エクスポートしてください")
    exit(1)

if not openai_api_key:
    logger.warning("OPENAI_API_KEYが設定されていません。OpenAI APIは使用できません。")

# OpenAI API設定
openai.api_key = openai_api_key

# 会話履歴の保存用
conversation_history = {}
MAX_HISTORY = 10  # 保存する会話の最大数

app = FastAPI()
slack_client = WebClient(token=slack_token)
signature_verifier = SignatureVerifier(signing_secret)

logger.info("アプリケーションを初期化しました")

# OpenHands agent tools
class OpenHandsTools:
    @staticmethod
    async def execute_bash(command: str, is_input: bool = False) -> Dict[str, Any]:
        """Execute a bash command and return the result"""
        try:
            if is_input:
                # 対話的なコマンドの処理（未実装）
                return {"error": "Interactive commands not supported yet"}

            # 危険なコマンドをブロック
            dangerous_commands = ["rm -rf", ":(){ :|:& };:", "> /dev/sda", "dd if=/dev/zero", "mv /* /dev/null"]
            for dangerous in dangerous_commands:
                if dangerous in command:
                    return {"error": f"危険なコマンドが検出されました: {dangerous}"}

            # 実行ディレクトリを制限
            allowed_dirs = os.environ.get("ALLOWED_DIRS", ".").split(",")
            current_dir = os.getcwd()
            is_allowed = False
            
            for allowed_dir in allowed_dirs:
                allowed_path = os.path.abspath(os.path.join(current_dir, allowed_dir))
                if command.startswith(("cd", "ls", "cat", "mkdir", "touch", "echo", "grep", "find")):
                    is_allowed = True
                    break
            
            if not is_allowed:
                logger.warning(f"許可されていないコマンドが実行されようとしました: {command}")
                # 本番環境では厳格に制限する場合はここでブロック
                # return {"error": "このコマンドは許可されていません"}

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
            # パスのバリデーション
            abs_path = os.path.abspath(path)
            current_dir = os.getcwd()
            allowed_dirs = os.environ.get("ALLOWED_DIRS", ".").split(",")
            
            # 許可されたディレクトリかチェック
            is_allowed = False
            for allowed_dir in allowed_dirs:
                allowed_path = os.path.abspath(os.path.join(current_dir, allowed_dir))
                if abs_path.startswith(allowed_path):
                    is_allowed = True
                    break
            
            if not is_allowed:
                return {"error": f"指定されたパスへのアクセスは許可されていません: {path}"}
            
            # ファイル拡張子のチェック
            allowed_extensions = [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".yml", ".yaml", ".env.example"]
            file_ext = os.path.splitext(path)[1].lower()
            
            if file_ext not in allowed_extensions:
                return {"error": f"指定されたファイル拡張子は許可されていません: {file_ext}"}
            
            # コマンドの実行
            if command == "view":
                if not os.path.exists(path):
                    return {"error": f"ファイルが存在しません: {path}"}
                with open(path, 'r') as f:
                    content = f.read()
                return {"content": content}
            elif command == "create":
                if os.path.exists(path):
                    return {"error": f"ファイル {path} は既に存在します"}
                
                # ディレクトリが存在しない場合は作成
                directory = os.path.dirname(path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                
                with open(path, 'w') as f:
                    f.write(file_text or "")
                logger.info(f"ファイルを作成しました: {path}")
                return {"message": f"ファイルを作成しました: {path}"}
            elif command == "str_replace":
                if not os.path.exists(path):
                    return {"error": f"ファイルが存在しません: {path}"}
                
                with open(path, 'r') as f:
                    content = f.read()
                
                if old_str not in content:
                    return {"error": f"指定された文字列がファイル内に見つかりません: {path}"}
                
                new_content = content.replace(old_str, new_str)
                with open(path, 'w') as f:
                    f.write(new_content)
                
                logger.info(f"ファイルを更新しました: {path}")
                return {"message": f"ファイルを更新しました: {path}"}
            else:
                return {"error": f"サポートされていないコマンドです: {command}"}
        except Exception as e:
            logger.error(f"ファイル操作中にエラーが発生しました: {str(e)}")
            return {"error": str(e)}

# OpenHands agent message handler
async def handle_openhands_message(message: str, channel_id: str, user_id: str = "user") -> None:
    """Handle messages using OpenHands agent functionality"""
    try:
        logger.info(f"Processing message with OpenHands agent: {message[:50]}...")

        # 会話履歴の取得または初期化
        if channel_id not in conversation_history:
            conversation_history[channel_id] = []

        # システムプロンプトを設定
        system_prompt = """あなたはOpenHands agentとして、以下の機能を提供します：
1. ファイルの表示・作成・編集
2. シェルコマンドの実行
3. GitHubとの連携

コマンドの実行方法：
コマンドを実行するには、必ず```bash```で囲んで指定してください。例：
```bash
ls -la
```

利用可能なツール：
- execute_bash: シェルコマンドを実行（```bash```で囲む必要あり）
- str_replace_editor: ファイルの操作（view, create, str_replace）

セキュリティ制限：
- 危険なコマンドは実行できません
- 特定のディレクトリ以外へのアクセスは制限されています
- コマンドは必ず```bash```で囲んで明示的に指定する必要があります
"""

        # メッセージを会話履歴に追加
        conversation_history[channel_id].append({"role": "user", "content": message})
        
        # 履歴が最大数を超えたら古いものを削除
        if len(conversation_history[channel_id]) > MAX_HISTORY:
            conversation_history[channel_id] = conversation_history[channel_id][-MAX_HISTORY:]

        if not openai_api_key:
            # OpenAI APIキーがない場合は、デモレスポンスを返す
            logger.warning("OpenAI API key is missing, returning demo response")
            ai_response = "OpenAI APIキーが設定されていないため、デモレスポンスを返しています。APIキーを設定してください。"
        else:
            # メッセージリストを作成
            messages = [{"role": "system", "content": system_prompt}]
            # 会話履歴を追加
            messages.extend(conversation_history[channel_id])
            
            # OpenAIを使用して応答を生成
            logger.debug(f"Sending request to OpenAI API with {len(messages)} messages")
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            # 応答を解析
            ai_response = response.choices[0].message.content
            logger.debug(f"Received response from OpenAI: {ai_response[:100]}...")
            
            # アシスタントの応答を会話履歴に追加
            conversation_history[channel_id].append({"role": "assistant", "content": ai_response})

        # コマンドの実行が必要な場合は実行
        if "```bash" in ai_response:
            # コマンドを抽出
            command = ai_response.split("```bash")[1].split("```")[0].strip()
            logger.info(f"Executing bash command: {command}")

            # コマンドを実行
            result = await OpenHandsTools.execute_bash(command)
            
            # 結果をSlackに送信
            if "error" in result:
                logger.error(f"Command execution error: {result['error']}")
                await send_slack_message(channel_id, f"エラーが発生しました：{result['error']}")
            else:
                output = result["stdout"] or result["stderr"]
                logger.info(f"Command executed successfully, exit code: {result.get('exit_code')}")
                await send_slack_message(channel_id, f"コマンド実行結果：\n```\n{output}\n```")
        else:
            # 通常の応答を送信
            logger.info("Sending standard response to Slack")
            await send_slack_message(channel_id, ai_response)

    except Exception as e:
        logger.error(f"Error in handle_openhands_message: {str(e)}")
        logger.exception(e)  # スタックトレースをログに出力
        await send_slack_message(channel_id, f"エラーが発生しました：{str(e)}")

# Slack message sender
async def send_slack_message(channel_id: str, text: str) -> None:
    """Send a message to Slack"""
    try:
        # SlackClientは非同期でないので、run_in_executorを使用して非同期化
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: slack_client.chat_postMessage(
                channel=channel_id,
                text=text
            )
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

    logger.debug(f"Received request to /slack/events from {request.client.host}")
    logger.debug(f"Headers: {dict(headers)}")
    
    # リクエストの署名を検証
    if not signature_verifier.is_valid_request(body, headers):
        logger.error(f"Invalid request signature from {request.client.host}")
        return {"error": "Invalid request signature"}

    # JSONデータを解析
    try:
        event_data = await request.json()
        logger.debug(f"Event data: {event_data}")
    except Exception as e:
        logger.error(f"Failed to parse request JSON: {e}")
        return {"error": "Invalid JSON"}

    # リクエストの検証
    if "challenge" in event_data:
        logger.info("Received Slack verification challenge")
        return {"challenge": event_data["challenge"]}

    # イベントの処理
    if "event" in event_data:
        event = event_data["event"]
        logger.info(f"Received event type: {event.get('type', 'unknown')}")

        # メッセージイベントの処理
        if event.get("type") == "message" and "bot_id" not in event:
            try:
                channel_id = event.get("channel")
                message = event.get("text", "")
                user_id = event.get("user", "unknown")
                
                logger.info(f"Received message from user {user_id} in channel {channel_id}: {message}")

                # メッセージを受信したことを通知
                await send_slack_message(
                    channel_id,
                    f"メッセージを受信しました: {message}\n処理を開始します..."
                )

                # OpenHands agentとしてメッセージを処理
                await handle_openhands_message(message, channel_id, user_id)

            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                logger.exception(e)  # スタックトレースをログに出力
        else:
            logger.debug(f"Ignored event: {event}")
    else:
        logger.debug("No event in request data")

    return {"status": "ok"}

# 会話履歴を削除するエンドポイント
@app.post("/api/clear-history")
async def clear_history(request: Request):
    try:
        data = await request.json()
        channel_id = data.get("channel_id")
        
        if not channel_id:
            return {"error": "channel_id is required"}
        
        if channel_id in conversation_history:
            conversation_history.pop(channel_id)
            logger.info(f"Cleared conversation history for channel {channel_id}")
            return {"status": "ok", "message": f"Conversation history cleared for channel {channel_id}"}
        else:
            return {"status": "ok", "message": "No history found for this channel"}
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return {"error": str(e)}

# システム情報エンドポイント
@app.get("/api/status")
async def system_status():
    try:
        # アクティブなチャンネル数
        active_channels = len(conversation_history)
        
        # メモリ使用量
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            "status": "running",
            "uptime": "不明",  # 今後実装予定
            "active_channels": active_channels,
            "memory_usage": {
                "rss": f"{memory_info.rss / 1024 / 1024:.2f} MB",
                "vms": f"{memory_info.vms / 1024 / 1024:.2f} MB"
            },
            "openai_api": "設定済み" if openai_api_key else "未設定"
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {"error": str(e)}

# ルートエンドポイント - 健全性チェック用
@app.get("/")
async def index():
    return {
        "status": "running",
        "message": "OpenHands Slack Bot is running. Use the /slack/events endpoint for Slack Event Subscriptions."
    }

# ngrokのURL検出
def get_ngrok_url():
    try:
        import requests
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            data = response.json()
            for tunnel in data["tunnels"]:
                if tunnel["proto"] == "https":
                    return tunnel["public_url"]
    except:
        pass
    return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 54725))
    
    # 起動情報の表示
    print(f"Starting OpenHands Slack Bot server on port {port}...")
    
    # ngrokのURLを検出
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"ngrok tunnel detected: {ngrok_url}")
        print(f"For Slack Event Subscriptions, use: {ngrok_url}/slack/events")
    else:
        print("No ngrok tunnel detected. Start ngrok with:")
        print(f"ngrok http {port}")
    
    # サーバー起動
    uvicorn.run(app, host="0.0.0.0", port=port)
