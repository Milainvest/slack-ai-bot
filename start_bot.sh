#!/bin/bash
# Openhandsボットを起動するスクリプト

# 色付きの出力用関数
print_green() {
    echo -e "\033[0;32m$1\033[0m"
}

print_yellow() {
    echo -e "\033[0;33m$1\033[0m"
}

print_red() {
    echo -e "\033[0;31m$1\033[0m"
}

# バナーを表示
print_green "================================================"
print_green "     Openhands Slack Bot 起動スクリプト         "
print_green "================================================"

# 環境変数ファイルの確認
if [ ! -f .env ]; then
    print_red "エラー: .envファイルが見つかりません。"
    print_yellow "以下の内容で.envファイルを作成してください:"
    echo "SLACK_BOT_TOKEN=xoxb-your-token-here"
    echo "SLACK_SIGNING_SECRET=your-signing-secret-here"
    echo "OPENAI_API_KEY=your-openai-api-key-here"
    echo "PORT=54725"
    echo "HOST=0.0.0.0"
    echo "ALLOWED_DIRS=."
    exit 1
fi

# 依存パッケージの確認とインストール
print_yellow "依存パッケージの確認中..."
if ! python3 -c "import fastapi, uvicorn, slack_sdk, openai, psutil" 2>/dev/null; then
    print_yellow "依存パッケージをインストールしています..."
    python3 -m pip install -r requirements.txt
else
    print_green "依存パッケージは既にインストールされています。"
fi

# サーバーの起動
print_green "Openhandsボットサーバーを起動しています..."
print_yellow "終了するには Ctrl+C を押してください。"
python3 slack_bot.py
