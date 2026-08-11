# nico_download

# What's this

- ニコニコ動画から検索して指定場所にdownloadするpython script
- depends on [nndownload](https://github.com/AlexAplin/nndownload)

# how to use

## installation

please use uv

```bash
$ uv sync
```

## edit config

- `cp config.toml.example config.toml`
- edit `config.toml` to set `session_cookie` and queries
- **`session_cookie` の設定が必要です (下記参照)**
- `uid` / `passwd` によるパスワードログインはニコニコ側の仕様変更 (CAPTCHA 導入) により現在動作しません。将来復旧した場合のフォールバックとしてフィールドだけ残しています (optional)

## session cookie の取得方法

ニコニコのログインシステム刷新 (CAPTCHA 導入) により、uid とパスワードによる自動ログインは動作しなくなりました。
代わりにブラウザでログインして取得した `user_session` クッキーを `config.toml` の `session_cookie` に設定してください。

1. ブラウザで <https://www.nicovideo.jp> にログインする
2. 開発者ツールを開く (Chrome / Firefox とも F12)
3. クッキー一覧を表示する
   - Chrome: `Application` タブ → 左側の `Storage` → `Cookies` → `https://www.nicovideo.jp`
   - Firefox: `ストレージ` タブ → `Cookie` → `https://www.nicovideo.jp`
4. `user_session` という名前のクッキーの値をコピーする
   (`user_session_12345678_0123456789abcdef...` のような文字列)
5. `config.toml` に貼り付ける

```toml
session_cookie = "user_session_12345678_0123456789abcdef..."
```

注意点:

- クッキーには有効期限があるため、認証エラーが出るようになったら再取得して更新してください
- ブラウザ側でログアウトするとクッキーが無効化されるので、ログアウトしないこと
- `user_session` はアカウントへのアクセス権そのものなので、`config.toml` を他人と共有しないこと

## run

```bash
$ uv run main.py --help  # to check flags
$ uv run main.py
```
