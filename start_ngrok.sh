#!/bin/bash
# ngrokを起動するスクリプト

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
print_green "     Openhands Slack Bot - ngrok起動スクリプト  "
print_green "================================================"

# ngrokがインストールされているか確認
if ! command -v ngrok &> /dev/null; then
    print_red "エラー: ngrokがインストールされていません。"
    print_yellow "ngrokをインストールするには、https://ngrok.com/download を参照してください。"
    exit 1
fi

# 環境変数からポート番号を取得
if [ -f .env ]; then
    PORT=$(grep PORT .env | cut -d '=' -f2)
fi

# ポート番号が設定されていない場合はデフォルト値を使用
if [ -z "$PORT" ]; then
    PORT=54725
    print_yellow "ポート番号が.envファイルで設定されていないため、デフォルト値(54725)を使用します。"
fi

print_green "ngrokを起動しています... (ポート: $PORT)"
print_yellow "終了するには Ctrl+C を押してください。"
print_yellow "重要: 以下に表示されるngrokのURLをSlack APIの設定ページで更新してください！"

# ngrokを起動
ngrok http $PORT
