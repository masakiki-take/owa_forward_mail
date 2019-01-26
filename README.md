# OWAメール転送システム
## 概要
 - Exchange Serverアカウントのメールボックスに受信した新着メッセージを転送します
 - 新着メッセージの転送内容は下記の3種類から選択可能です
   - 件数: 件数のみ通知
   - 差出人と件名: 差出人と件名の一覧を通知
   - 全文: メールをそのまま転送
 - パスワード変更などによりExchange Serverアカウントの認証が行えなくなった場合は、認証失敗の通知メールを送信し、最新のパスワードでログインするまで転送停止状態になります

## 開発環境構築
### DB
Postgresqlで下記ユーザーとDBを作成
 - User: owa_user
 - Password: owa_password
 - Database: owa_db

### 環境変数
```
PERSONAL_CRYPTO_KEY=''    # 個人情報暗号化キー
EMAIL_AUTH_CRYPTO_KEY=''  # メール認証トークン暗号化キー
SECRET_KEY=''             # CSRF_TOKEN などセキュリティキーとして利用される定数
SLACK_TOKEN               # Slack APIトークン
SLACK_CHANNEL             # Slackチャンネル名 (ログ通知用)
SLACK_USERNAME            # Slack BOTユーザー名
SLACK_ICON_EMOJI          # Slack BOTアイコン絵文字
```

### pip install
```
$ cd /path/to/owa_forward_mail/
$ pip install -r requirements.txt
```

### migrate
```
$ python manage.py migrate --settings=owa_forward_mail.settings.development
```

### runserver
```
$ python manage.py runserver 127.0.0.1:5500 --settings=owa_forward_mail.settings.development
```

### タスク実行
```
$ python manage.py runtask --settings=owa_forward_mail.settings.development
```
