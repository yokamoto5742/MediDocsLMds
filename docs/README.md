# 退院時サマリ作成アプリ

このアプリケーションは、生成AIを活用して退院時サマリや現病歴などの医療文書を効率的に作成するためのWebアプリケーションです。

## 主な機能

### 📋 文書作成機能
- **退院時サマリ**、**現病歴**の自動生成
- 生成結果は「全文」「入院期間」「現病歴」「入院時検査」「入院中の治療経過」「退院申し送り」「備考」のタブ形式で表示

### 🤖 複数AIモデル対応
- **Claude** (Anthropic Amazon Bedrock)
- **Gemini** (Google Vertex AI)
- 入力文字数に応じた自動モデル切り替え機能（Claude → Gemini Pro）

### ⚙️ カスタマイズ機能
- 診療科別、医師別、文書タイプごとの専用プロンプト設定
- AIモデルの選択・設定保存
- ユーザー設定の自動保存・復元

### 📊 統計・管理機能
- 使用状況の統計表示（作成件数、トークン使用量、処理時間）
- 期間・モデル・文書タイプ・診療科・医師別での絞り込み表示
- PostgreSQLによるデータ永続化

## システム要件

### 必要なソフトウェア
- Python 3.11以上
- PostgreSQL 16以上

### 必要な認証情報
以下のいずれか1つ以上の認証情報が必要です：
- **Amazon Bedrock + Claude**: AWS認証情報（AWS Access Key ID, Secret Access Key）
- **Vertex AI + Gemini**: Google Cloud認証情報（Service Account JSON）

## インストール手順

### 1. リポジトリのクローン
```bash
git clone <リポジトリURL>
cd medical-summary-app
```

### 2. 仮想環境の作成（推奨）
```bash
python -m venv venv
# Windows
venv\Scripts\activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. Google Cloud認証設定（Vertex AI使用時）
Vertex AI + Geminiを使用する場合、Google Cloud Service Account JSONを取得します：

1. [Google Cloud Console](https://console.cloud.google.com/) → プロジェクト選択
2. 「APIとサービス」→「ライブラリ」で「Vertex AI API」を有効化
3. 「認証情報」→「サービスアカウント」で新規作成
4. 「Vertex AI User」権限を付与
5. 「キー」タブで新しいJSON形式のキーを作成
6. ダウンロードしたJSONの内容を `GOOGLE_CREDENTIALS_JSON` 環境変数に設定

### 5. 環境変数の設定
`.env`ファイルを作成し、以下の設定を行ってください：

```env
# データベース設定（PostgreSQL）
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# AI API設定（いずれか1つ以上設定）
# Amazon Bedrock + Claude
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=ap-northeast-1
ANTHROPIC_MODEL=apac.anthropic.claude-sonnet-4-20250514-v1:0

# Vertex AI + Gemini API
GOOGLE_CREDENTIALS_JSON=your_JSON_key
GOOGLE_PROJECT_ID=your-google-cloud-project-id
GOOGLE_LOCATION=us-west1
GEMINI_MODEL=gemini-2.0-flash-thinking-exp
GEMINI_THINKING_LEVEL=HIGH

# トークン制限設定
MAX_INPUT_TOKENS=300000
MIN_INPUT_TOKENS=100
MAX_TOKEN_THRESHOLD=100000

# データベース接続プール設定
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# アプリケーション設定
APP_TYPE=dischargesummary
```

## 使用方法

### アプリケーションの起動
```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセス

### 基本的な使い方

#### 1. 文書作成
1. **サイドバー**で診療科、医師名、文書タイプ、AIモデルを選択
2. **退院時処方**を入力（任意）
3. **カルテ記載**にカルテ情報を入力
4. **追加情報**に補足情報を入力（任意）
5. **「作成」ボタン**をクリック
6. 生成された文書をタブ別に確認・コピー

#### 2. プロンプト管理
1. サイドバーの**「プロンプト管理」**をクリック
2. 文書名、診療科、医師名、AIモデルを選択
3. プロンプト内容を編集
4. **「保存」**をクリック
5. 不要なプロンプトは**「プロンプトを削除」**で削除可能

#### 3. 統計情報確認
1. サイドバーの**「統計情報」**をクリック
2. 期間、AIモデル、文書名で絞り込み
3. 診療科・医師別の使用状況と詳細レコードを確認

## 設定カスタマイズ

診療科・医師・文書タイプのカスタマイズは `utils/constants.py` で管理されています：

```python
DEFAULT_DEPARTMENT = ["default", "内科", "消化器内科", "整形外科"]

DEPARTMENT_DOCTORS_MAPPING = {
    "default": ["default"],
    "内科": ["default", "医師A", "医師B"]
}

DOCUMENT_TYPES = ["退院時サマリ", "現病歴"]

DEFAULT_SECTION_NAMES = ["入院期間", "現病歴", "入院時検査", "治療経過", "退院申し送り", "備考"]
```

また、プロンプト管理ページから診療科・医師ごとのカスタムプロンプトを設定できます。

## 開発者向け情報

### 開発・テスト環境
```bash
# テスト実行（全テスト）
pytest --cov=. tests/

# 特定テストファイルの実行
pytest tests/test_summary_service.py

# 詳細出力でテスト実行
pytest -v tests/

# 型チェック
pyright
```

### プロジェクト構造
```
├── app.py                                 # メインアプリケーション
├── CLAUDE.md                              # 開発ガイドライン
├── Procfile                               # Heroku用設定
├── pyrightconfig.json                     # 型チェック設定
├── requirements.txt                       # Python依存関係
├── setup.sh                               # Streamlit設定
├── database/                              # データベース関連
│   ├── db.py                              # DB接続管理
│   ├── models.py                          # SQLAlchemyモデル
│   └── schema.py                          # テーブル管理
├── external_service/                      # 外部API連携
│   ├── api_factory.py                     # APIファクトリー
│   ├── base_api.py                        # 基底APIクラス（抽象クラス）
│   ├── claude_api.py                      # Claude API（AWS Bedrock）
│   ├── gemini_api.py                      # Gemini API（Vertex AI）
│   └── gemini_evaluation.py               # 出力評価用API
├── services/                              # ビジネスロジック
│   ├── evaluation_service.py              # 評価サービス
│   └── summary_service.py                 # サマリー作成サービス
├── ui_components/                         # UIコンポーネント
│   └── navigation.py                      # ナビゲーション・ユーザー設定
├── utils/                                 # ユーティリティ
│   ├── config.py                          # 設定管理
│   ├── constants.py                       # 定数定義
│   ├── error_handlers.py                  # エラーハンドリング
│   ├── exceptions.py                      # 例外クラス
│   ├── prompt_manager.py                  # プロンプト管理
│   └── text_processor.py                  # テキスト処理
└── views/                                 # ページビュー
    ├── main_page.py                       # メインページ
    ├── prompt_management_page.py          # プロンプト管理
    ├── statistics_page.py                 # 統計情報表示
    └── evaluation_settings_page.py        # 評価設定
```

### データベーステーブル
- **prompts**: プロンプト管理（診療科・医師・文書タイプ別）
- **summary_usage**: 使用統計（トークン数・処理時間記録）
- **app_settings**: アプリケーション設定（ユーザー設定保存）

### APIクライアント追加
新しいAIプロバイダーを追加する場合：

1. `external_service/`に新しいAPIクライアントを作成
2. `BaseAPIClient`を継承
3. `api_factory.py`にプロバイダーを追加

### 主要機能

#### 自動モデル切り替え
- Claude選択時に入力テキストが設定トークン数を超える場合、自動的にGeminiに切り替え
- 切り替え時にはユーザーに通知表示

#### プロンプト階層管理
- 診療科・医師・文書タイプの組み合わせでプロンプトを管理
- デフォルトプロンプトからの継承機能

#### 統計データ分析
- 時系列での使用状況追跡
- モデル別・診療科別・医師別の詳細分析
- トークン使用量と処理時間の管理

## 最新の変更

変更履歴は [docs/CHANGELOG.md](CHANGELOG.md) を参照してください。

## トラブルシューティング

### よくある問題と解決方法

| 問題 | 原因 | 対処法 |
|------|------|------|
| データベース接続エラー | PostgreSQL未起動、環境変数未設定 | `DATABASE_URL`を確認し、PostgreSQLサービスを起動 |
| API認証エラー | AWS/Google認証情報が不正 | AWS Access Key、`GOOGLE_CREDENTIALS_JSON`を再確認 |
| トークン数超過エラー | 入力テキストが上限超過 | 入力を短縮するか`MAX_TOKEN_THRESHOLD`を調整 |
| Streamlit起動エラー | ポート競合または設定エラー | `streamlit run app.py --logger.level=debug`で詳細確認 |

### パフォーマンス最適化
- **DB**: `DB_POOL_SIZE`（デフォルト5）を調整
- **API**: プロンプト最適化によるトークン削減

## ライセンスと免責

このプロジェクトは [Apache License 2.0](LICENSE) のもとで公開されています。

このアプリケーションは医療文書作成の支援ツールです。生成された文書は医療従事者による確認・承認が必須です。本ソフトウェアの使用により生じた損害について、開発者は責任を負いません。
