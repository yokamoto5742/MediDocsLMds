# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さな関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述します。文末に"。"や"."をつけないでください。

## Project Overview

This is a Streamlit-based medical documentation application (退院時サマリ作成アプリ - Discharge Summary Creation App) that generates hospital discharge summaries using multiple AI providers (Gemini via Vertex AI and Claude via AWS Bedrock).

## Development Commands

### Running the Application
```bash
streamlit run app.py
```

### Testing
```bash
# Run all tests with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_summary_service.py

# Run tests with verbose output
pytest -v tests/
```

### Type Checking
```bash
pyright
```
Type checking is configured in `pyrightconfig.json` and covers `services`, `utils`, `ui_components`, and `views` directories.

### Environment Setup
The application requires a `.env` file with the following credentials:
- PostgreSQL: `DATABASE_URL` or individual `POSTGRES_*` variables
- AWS Bedrock (Claude): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ANTHROPIC_MODEL`
- Vertex AI (Gemini): `GOOGLE_PROJECT_ID`, `GOOGLE_CLOUD_LOCATION`, `GEMINI_MODEL`, `GOOGLE_CREDENTIALS_JSON`

## Architecture

### Core Data Flow
1. User inputs medical chart data through the main page UI (`views/main_page.py`)
2. Input is validated and processed by `services/summary_service.py`
3. API provider (Gemini or Claude) is selected via factory pattern (`external_service/api_factory.py`)
4. AI generates structured medical summary using department-specific prompts
5. Results are parsed, displayed, and optionally saved to PostgreSQL database

### Key Components

**API Provider Architecture**
- `external_service/base_api.py`: Abstract base class `BaseAPIClient` defining the contract for all AI providers
- `external_service/gemini_api.py`: Vertex AI Gemini implementation
- `external_service/claude_api.py`: AWS Bedrock Claude implementation
- `external_service/api_factory.py`: Factory pattern using `APIProvider` enum to instantiate the appropriate client

**Service Layer**
- `services/summary_service.py`: Orchestrates summary generation workflow including validation, API selection, token threshold management (auto-switches to Gemini for long inputs), and database persistence
- `services/evaluation_service.py`: Handles evaluation of generated summaries using AI

**Database Layer**
- `database/db.py`: `DatabaseManager` class handles all PostgreSQL operations using SQLAlchemy
- `database/models.py`: SQLAlchemy ORM models
- `database/schema.py`: Database schema definitions

**Configuration & Utilities**
- `utils/config.py`: Loads configuration from `config.ini` and parses `DATABASE_URL`
- `utils/prompt_manager.py`: Manages department/doctor/document-type-specific prompts stored in database
- `utils/text_processor.py`: Parses AI output into structured sections using aliases (病名→診断名, 症状→臨床経過, etc.)
- `utils/constants.py`: Centralized message strings and UI constants
- `utils/error_handlers.py`: Decorator-based error handling for Streamlit

**UI Components**
- `views/main_page.py`: Main summary generation interface
- `views/prompt_management_page.py`: CRUD interface for customizing prompts
- `views/statistics_page.py`: Usage statistics dashboard
- `views/evaluation_settings_page.py`: Configure evaluation criteria
- `ui_components/navigation.py`: Page navigation and user settings persistence

### State Management
Streamlit session state stores:
- `output_summary`: Raw AI response
- `parsed_summary`: Structured dictionary of sections
- `selected_department`, `selected_model`, `selected_doctor`: User preferences
- `current_page`: Navigation state ("main", "prompt_edit", "statistics", "evaluation_settings")

### Prompt System
Prompts are customizable per department, document type, and doctor, stored in PostgreSQL with fallback to default config. The system supports:
- Department-specific clinical context (循環器, 呼吸器, etc.)
- Document types (退院時サマリ, 主治医意見書)
- Doctor-specific preferences

### Testing Strategy
Tests use pytest with fixtures in `conftest.py`:
- `suppress_streamlit_warnings`: Reduces log noise
- `temp_config_file`, `temp_env_file`: Temporary configuration
- `mock_database_manager`: Database mocking
- `cleanup_magicmock_dirs`: Cleans up test artifacts
