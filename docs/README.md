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
Vertex AI + Geminiを使用する場合は、Google Cloud Service Accountを作成し、認証情報を取得します：

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクトを作成または選択
3. 「APIとサービス」→「認証情報」に移動
4. 「認証情報を作成」→「サービスアカウント」を選択
5. サービスアカウント名を入力し、作成
6. Vertex AI APIを有効化：「APIとサービス」→「ライブラリ」で「Vertex AI API」を検索し有効化
7. 作成したサービスアカウントに以下の権限を付与：
   - `Vertex AI User`
   - `AI Platform Developer`
8. 「キー」タブで「キーを追加」→「新しいキーを作成」→「JSON」を選択
9. ダウンロードしたJSONファイルの内容を`GOOGLE_CREDENTIALS_JSON`環境変数に設定

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

### 診療科・医師の追加
`utils/constants.py`の以下の部分を編集：

```python
DEFAULT_DEPARTMENT = ["default", "内科", "消化器内科", "整形外科"]

DEPARTMENT_DOCTORS_MAPPING = {
    "default": ["default", "医師共通"],
    "内科": ["default", "田中医師", "佐藤医師"],
    "整形外科": ["default", "鈴木医師"]
}
```

### 文書タイプの追加
```python
DOCUMENT_TYPES = ["退院時サマリ", "現病歴"]
DEFAULT_DOCUMENT_TYPE = "退院時サマリ"
```

### セクション名のカスタマイズ
```python
DEFAULT_SECTION_NAMES = [
    "入院期間", "現病歴", "入院時検査", 
    "入院中の治療経過", "退院申し送り", "備考"
]
```

## 開発者向け情報

### 開発・テスト環境
```bash
# テスト実行
python -m pytest tests/ -v

# カバレッジ付きテスト
python -m pytest tests/ -v --cov=. --cov-report=html

```

### プロジェクト構造
```
├── app.py                        # メインアプリケーション
├── config.ini                    # 設定ファイル
├── Procfile                      # Heroku用設定
├── requirements.txt              # Python依存関係
├── runtime.txt                   # Python実行環境
├── setup.sh                     # Streamlit設定
├── database/                     # データベース関連
│   ├── db.py                     # DB接続管理
│   ├── models.py                 # SQLAlchemyモデル
│   ├── repositories.py           # データアクセス層
│   └── schema.py                 # テーブル管理
├── external_service/             # 外部API連携
│   ├── api_factory.py            # APIファクトリー
│   ├── base_api.py               # 基底APIクラス
│   ├── claude_api.py             # Claude API
│   └── gemini_api.py             # Gemini API
├── services/                     # ビジネスロジック
│   ├── generation_service.py     # 文書生成サービス
│   ├── model_service.py          # モデル管理サービス
│   ├── statistics_service.py     # 統計サービス
│   ├── summary_service.py        # サマリー作成サービス
│   └── validation_service.py     # バリデーションサービス
├── ui_components/                # UIコンポーネント
│   └── navigation.py             # ナビゲーション・設定
├── utils/                        # ユーティリティ
│   ├── config.py                 # 設定管理
│   ├── constants.py              # 定数定義
│   ├── env_loader.py             # 環境変数読み込み
│   ├── error_handlers.py         # エラーハンドリング
│   ├── exceptions.py             # 例外クラス
│   ├── prompt_manager.py         # プロンプト管理
│   └── text_processor.py         # テキスト処理
└── views/                        # ページビュー
    ├── main_page.py              # メインページ
    ├── prompt_management_page.py # プロンプト管理
    └── statistics_page.py        # 統計ページ
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
- Claude選択時に入力テキストが設定された文字数を超える場合、自動的にGemini_Proに切り替え
- 切り替え時にはユーザーに通知表示

#### プロンプト階層管理
- 診療科・医師・文書タイプの組み合わせでプロンプトを管理
- デフォルトプロンプトからの継承機能

#### 統計データ分析
- 時系列での使用状況追跡
- モデル別・診療科別・医師別の詳細分析
- トークン使用量と処理時間の管理

### テスト状況
- 最近修正されたテスト:
  - `tests/external_service/test_gemini_api.py` - GOOGLE_CREDENTIALS_JSON認証対応
  - `tests/services/test_model_service.py` - 認証情報変数名更新
  - `tests/services/test_validation_service.py` - 認証チェック更新
  - `tests/services/test_summary_service.py` - datetime mocking問題を解決
  - `tests/utils/test_text_processor.py` - inline content parsing issue解決
- カバレッジレポート利用可能

### 開発者体験向上
- **自動通知システム**: 作業完了時のデスクトップ通知
- **hooks設定**: Claude Code終了時の自動通知
- **手動通知**: 任意のタイミングでの通知実行
- **統合開発環境**: CLAUDE.md による開発コマンド整備

## 変更履歴

### v2.1.0 (2025-09-15) - Vertex AI認証統合
#### 🔄 認証システム変更
- **BREAKING CHANGE**: `GEMINI_CREDENTIALS` → `GOOGLE_CREDENTIALS_JSON`に変更
- Google Cloud Service Account JSON認証に移行
- 新規環境変数追加: `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION`
- Vertex AI APIとの完全統合

#### 🛠️ コード改善
- `external_service/gemini_api.py`: Service Account認証ロジック実装
- `utils/config.py`: 認証設定変数更新
- `services/`: 全サービスクラスの認証チェック更新
- `ui_components/navigation.py`: UI認証状態表示更新

#### 🧪 テスト更新
- 全247テストが新しい認証方式に対応
- `test_gemini_api.py`: Service Accountモック実装
- 認証関連テストケースの comprehensive更新

#### 📚 ドキュメント更新
- README.md: Google Cloud Service Account取得手順追加
- 環境変数設定例更新
- Herokuデプロイ手順更新
- トラブルシューティング強化

#### 🔧 後方互換性
- 環境変数`GOOGLE_CREDENTIALS_JSON`未設定時は従来の認証方式を使用
- 段階的移行をサポート

## デプロイメント

### Herokuデプロイ
このアプリケーションはHerokuへのデプロイに対応しています。

1. Heroku CLIをインストール
2. Herokuアプリを作成
3. PostgreSQLアドオンを追加
4. 環境変数を設定
5. デプロイ実行

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku config:set AWS_ACCESS_KEY_ID=your_aws_access_key_id
heroku config:set AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
heroku config:set AWS_REGION=ap-northeast-1
heroku config:set ANTHROPIC_MODEL=apac.anthropic.claude-sonnet-4-20250514-v1:0
heroku config:set GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project",...}'
heroku config:set GOOGLE_PROJECT_ID=your-google-cloud-project-id
heroku config:set GOOGLE_LOCATION=us-west1
git push heroku main
```

## トラブルシューティング

### よくある問題

#### データベース接続エラー
- PostgreSQLサービスが起動しているか確認
- 環境変数の設定を再確認
- データベースとユーザーの権限を確認

#### API認証エラー
- AWS認証情報（Access Key, Secret Key）が正しく設定されているか確認
- Google Cloud Service Account JSONが正しく設定されているか確認
- `GOOGLE_PROJECT_ID`と`GOOGLE_LOCATION`が設定されているか確認
- Service AccountにVertex AI APIの権限が付与されているか確認
- APIの有効期限と使用制限を確認
- ネットワーク接続を確認

#### トークン数超過エラー
- 入力テキストの長さを調整
- `MAX_TOKEN_THRESHOLD`の値を調整
- Vertex AI + Gemini APIを有効にして自動切り替えを利用

### パフォーマンス最適化

#### データベース最適化
- コネクションプールサイズの調整（`DB_POOL_SIZE`）
- クエリインデックスの最適化

#### API使用量最適化
- プロンプトの最適化によるトークン削減
- 適切なモデル選択による効率化

### ライセンス
このプロジェクトは[Apache License 2.0](docs/LICENSE)のもとで公開されています。

### 免責事項
このアプリケーションは医療文書作成の支援ツールです。生成された文書は必ず医療従事者による確認・承認を経てご使用ください。本ソフトウェアの使用により生じたいかなる損害についても、開発者は責任を負いません。