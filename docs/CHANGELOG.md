# Changelog

このプロジェクトにおけるすべての重要な変更を記録します。

フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## [1.0.0] - 2026-01-13

### Added
- CLAUDE.mdファイルを追加し、AI作業ガイダンスを提供
- 退院時サマリの評価プロンプト機能
- `DOCUMENT_TYPE_OPTIONS`定数を追加し、文書タイプの選択肢を明確化
- テキストプロセッサにセクションエイリアス（病名、症状、処方など）を追加
- 退院時処方をプロンプトに含める機能
- 新しい定数を追加し、既存の定数を整理

### Changed
- `previous_record`を`current_prescription`にリネームし、より明確な命名に変更
  - `evaluation_service.py`
  - `base_api.py`
  - `api_factory.py`
  - `summary_service.py`
  - `main_page.py`
- アプリケーションのページタイトルを「退院時サマリ作成アプリ」に変更
- 前回の記載を現在の処方に変更し、UI表示を改善
- 退院時処方がない場合でも追加情報を含めるようにプロンプトを改善

### Removed
- デフォルト医師リストから"医師共通"を削除

### Fixed
- デフォルト医師が1人のみの場合、医師選択UIを非表示にするように改善

### Tests
- `evaluation_service`のテストを`current_prescription`への名前変更に対応

---

## Initial Release

### Added
- Streamlitベースの医療文書作成アプリケーション
- 複数AIプロバイダー対応（Gemini via Vertex AI、Claude via AWS Bedrock）
- PostgreSQLデータベース統合
- 診療科・医師・文書タイプごとのカスタマイズ可能なプロンプトシステム
- 使用統計ダッシュボード
- プロンプト管理CRUD機能
- 評価設定ページ
- テストスイート（pytest）
- 型チェック（pyright）
