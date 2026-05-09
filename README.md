# Corporate News Monitor

指定企業のニュース・開示情報を自動収集し、メールで通知するシステムです。

## 収集ソース

| ソース | 内容 | 更新頻度 |
|--------|------|----------|
| Google News | 一般ニュース・メディア報道 | リアルタイム |
| EDINET | 有価証券報告書・全開示書類 | 随時 |
| TDnet（適時開示） | 東証適時開示情報 | 随時 |
| 企業IRページ | 各社IRのRSSフィード（任意設定） | 随時 |

---

## セットアップ手順

### 1. GitHubリポジトリを作成する

- GitHub で新しいリポジトリを作成
- このフォルダの内容をすべてプッシュ

```bash
cd corporate-news-monitor
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/あなたのユーザー名/corporate-news-monitor.git
git push -u origin main
```

> **注意（Privateリポジトリの場合）**
> GitHub Actions の無料枠は Private リポジトリで 2,000分/月です。
> 30分間隔 × 実行2分 = 約2,880分/月となり超過する可能性があります。
> **Publicリポジトリ推奨**（Actions 無料・無制限）または 60分間隔への変更をご検討ください。

---

### 2. GitHub Secrets を設定する

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で以下を登録：

| Secret名 | 内容 |
|----------|------|
| `GMAIL_USER` | 送信元Gmailアドレス（例: yourname@gmail.com） |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード（後述） |
| `EMAIL_TO` | 通知先メールアドレス |
| `ANTHROPIC_API_KEY` | Anthropic API キー（要約・重要度判定に使用） |

#### Gmail アプリパスワードの取得方法
1. Google アカウント → セキュリティ → 2段階認証を有効化
2. セキュリティ → アプリパスワード → 「メール」で生成
3. 生成された16文字のパスワードを `GMAIL_APP_PASSWORD` に設定

---

### 3. 監視企業リストを設定する

`companies.json` を編集して対象企業を追加します：

```json
[
  {
    "name": "トヨタ自動車",
    "code": "7203",
    "ir_rss_url": ""
  },
  {
    "name": "ソニーグループ",
    "code": "6758",
    "ir_rss_url": "https://www.sony.com/ja/SonyInfo/IR/rss.xml"
  }
]
```

- `name`: 企業名（EDINET・Google Newsの検索に使用）
- `code`: 証券コード4桁（TDnet・EDINETのフィルタリングに使用）
- `ir_rss_url`: 企業IRページのRSSフィード URL（任意。未設定の場合は空文字）

---

### 4. 動作確認

GitHub の **Actions タブ → Corporate News Monitor → Run workflow** で手動実行できます。

---

## メール通知のサンプル

- 重要度が **高**（決算・M&A・行政処分など）は赤バッジ
- 重要度が **中**（新製品・提携など）は黄バッジ
- 重要度が **低**（一般情報）は灰バッジ
- 件名に `[重要]` / `[通常]` プレフィックスがつくため受信トレイで識別しやすい

---

## ファイル構成

```
corporate-news-monitor/
├── .github/workflows/monitor.yml   # GitHub Actions 定義
├── companies.json                  # 監視企業リスト（編集してください）
├── seen_ids.json                   # 既出記事ID（自動管理）
├── requirements.txt
└── src/
    ├── main.py                     # エントリポイント
    ├── summarizer.py               # Claude API による要約・重要度判定
    ├── notifier.py                 # メール送信
    └── sources/
        ├── google_news.py          # Google News RSS
        ├── edinet.py               # EDINET API
        ├── tdnet.py                # TDnet 適時開示スクレイピング
        └── company_ir.py          # 企業IR RSSフィード
```

---

## 実行間隔の変更

`.github/workflows/monitor.yml` の `cron` を変更します：

```yaml
- cron: '*/30 * * * *'   # 30分ごと
- cron: '0 * * * *'      # 1時間ごと
- cron: '0 8,12,17 * * *' # 8時・12時・17時（平日のみにしたい場合は別途設定）
```
