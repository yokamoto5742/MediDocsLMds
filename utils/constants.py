MESSAGES = {
    "PROMPT_UPDATED": "プロンプトを更新しました",
    "PROMPT_CREATED": "プロンプトを新規作成しました",
    "PROMPT_DELETED": "プロンプトを削除しました",

    "NO_DATA_FOUND": "指定期間のデータがありません",

    "FIELD_REQUIRED": "すべての項目を入力してください",
    "NO_INPUT": "⚠️ カルテ情報を入力してください",
    "INPUT_TOO_SHORT": "⚠️ 入力テキストが短すぎます",
    "INPUT_TOO_LONG": "⚠️ 入力テキストが長すぎます",
    "TOKEN_THRESHOLD_EXCEEDED": "⚠️ 入力テキストが長いため{original_model} から Gemini_Pro に切り替えます",
    "TOKEN_THRESHOLD_EXCEEDED_NO_GEMINI": "⚠️ Gemini APIの認証情報が設定されていないため処理できません。",

    "API_CREDENTIALS_MISSING": "⚠️ Gemini APIの認証情報が設定されていません。環境変数を確認してください。",
    "NO_API_CREDENTIALS": "⚠️ 使用可能なAI APIの認証情報が設定されていません。環境変数を確認してください。",

    "VERTEX_AI_PROJECT_MISSING": "⚠️ GOOGLE_PROJECT_ID環境変数が設定されていません。",
    "VERTEX_AI_INIT_ERROR": "Vertex AI Gemini API初期化エラー: {error}",
    "VERTEX_AI_API_ERROR": "Vertex AI Gemini API呼び出しエラー: {error}",
    "VERTEX_AI_CREDENTIALS_JSON_PARSE_ERROR": "GOOGLE_CREDENTIALS_JSON環境変数の解析エラー: {error}",
    "VERTEX_AI_CREDENTIALS_FIELD_MISSING": "認証情報に必要なフィールドが不足: {error}",
    "VERTEX_AI_CREDENTIALS_ERROR": "認証情報の作成エラー: {error}",

    "AWS_CREDENTIALS_MISSING": "⚠️ AWS認証情報が設定されていません。環境変数を確認してください。",
    "ANTHROPIC_MODEL_MISSING": "⚠️ ANTHROPIC_MODELが設定されていません。環境変数を確認してください。",
    "BEDROCK_INIT_ERROR": "Amazon Bedrock Claude API初期化エラー: {error}",
    "BEDROCK_API_ERROR": "Amazon Bedrock Claude API呼び出しエラー: {error}",

    "EMPTY_RESPONSE": "レスポンスが空です",

    "UNSUPPORTED_API_PROVIDER": "未対応のAPIプロバイダー: {provider}",

    "DATABASE_URL_PARSE_ERROR": "DATABASE_URLの解析に失敗しました: {error}",
    "DATABASE_CONNECTION_INFO_MISSING": "PostgreSQL接続情報が設定されていません。環境変数または設定ファイルを確認してください。",
    "DATABASE_CONNECTION_ERROR": "PostgreSQLへの接続に失敗しました: {error}",
    "DATABASE_NOT_INITIALIZED": "データベース接続が初期化されていません",
    "DATABASE_QUERY_ERROR": "クエリ実行中にエラーが発生しました: {error}",
    "DATABASE_GET_RECORD_ERROR": "レコード取得中にエラーが発生しました: {error}",
    "DATABASE_INSERT_ERROR": "レコード挿入中にエラーが発生しました: {error}",
    "DATABASE_UPDATE_ERROR": "レコード更新中にエラーが発生しました: {error}",
    "DATABASE_UPSERT_ERROR": "レコードのupsert中にエラーが発生しました: {error}",
    "DATABASE_DELETE_ERROR": "レコード削除中にエラーが発生しました: {error}",
    "DATABASE_COUNT_ERROR": "カウント実行中にエラーが発生しました: {error}",
    "DATABASE_TABLE_CREATE_ERROR": "テーブル作成中にエラーが発生しました: {error}",
    "DATABASE_INIT_FAILED": "データベースの初期化に失敗しました: {error}",

    "COPY_INSTRUCTION": "💡 テキストエリアの右上にマウスを合わせて左クリックでコピーできます",
    "PROCESSING_TIME": "⏱️ 処理時間: {processing_time:.0f}秒",
    "EVALUATION_COMPLETED": "評価が完了しました。画面を下までスクロールしてください。",
}

TAB_NAMES = {
    "ALL": "全文",
    "ADMISSION_PERIOD": "【入院期間】",
    "CURRENT_ILLNESS": "【現病歴】",
    "ADMISSION_TESTS": "【入院時検査】",
    "TREATMENT_PROGRESS": "【入院中の治療経過】",
    "DISCHARGE_NOTES": "【退院申し送り】",
    "NOTE": "【備考】"
}

DEFAULT_DEPARTMENT = ["default","内科", "消化器内科", "整形外科"]
DEFAULT_DOCTOR = ["default"]
DEPARTMENT_DOCTORS_MAPPING = {
    "default": ["default"],
}

DEFAULT_DOCUMENT_TYPE = "退院時サマリ"
DOCUMENT_TYPES = ["退院時サマリ", "現病歴"]
DOCUMENT_TYPE_OPTIONS = ["退院時サマリ", "現病歴", "すべて"]
MODEL_OPTIONS =  ["すべて", "Claude", "Gemini_Pro"]

DEFAULT_SECTION_NAMES = [
    "入院期間", "現病歴", "入院時検査", "入院中の治療経過", "退院申し送り", "備考"
]

# 【治療経過】: 内容 など(改行含む)
# 治療経過: 内容 など(改行含む)
# 治療経過（行全体がセクション名のみ）
SECTION_DETECTION_PATTERNS = [
    r'^[【\[■●\s]*{section}[】\]\s]*[::]?\s*(.*)$',
    r'^{section}\s*[::]?\s*(.*)$',
    r'^{section}\s*$',
]
