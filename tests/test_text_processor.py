from unittest.mock import patch

from utils.text_processor import format_output_summary, parse_output_summary, section_aliases


class TestFormatOutputSummary:
    """format_output_summary関数のテスト"""
    
    def test_remove_asterisks(self):
        """アスタリスクの除去テスト"""
        input_text = "これは*テスト*です"
        expected = "これはテストです"
        result = format_output_summary(input_text)
        assert result == expected
    
    def test_remove_japanese_asterisks(self):
        """日本語アスタリスクの除去テスト"""
        input_text = "これは＊テスト＊です"
        expected = "これはテストです"
        result = format_output_summary(input_text)
        assert result == expected
    
    def test_remove_hash_symbols(self):
        """ハッシュ記号の除去テスト"""
        input_text = "#見出し# テスト"
        expected = "見出しテスト"
        result = format_output_summary(input_text)
        assert result == expected
    
    def test_remove_spaces(self):
        """半角スペースの除去テスト"""
        input_text = "これは テスト です"
        expected = "これはテストです"
        result = format_output_summary(input_text)
        assert result == expected
    
    def test_remove_all_symbols(self):
        """すべての記号の除去テスト"""
        input_text = "# これは * テスト ＊ です #"
        expected = "これはテストです"
        result = format_output_summary(input_text)
        assert result == expected
    
    def test_empty_string(self):
        """空文字列のテスト"""
        input_text = ""
        expected = ""
        result = format_output_summary(input_text)
        assert result == expected
    
    def test_only_symbols(self):
        """記号のみの文字列テスト"""
        input_text = "* ＊ # "
        expected = ""
        result = format_output_summary(input_text)
        assert result == expected
    
    def test_multiple_consecutive_symbols(self):
        """連続する記号のテスト"""
        input_text = "***テスト###"
        expected = "テスト"
        result = format_output_summary(input_text)
        assert result == expected


class TestParseOutputSummary:
    """parse_output_summary関数のテスト"""
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_simple_section_parsing(self):
        """基本的なセクション解析テスト"""
        input_text = """入院期間: 2024/01/01～2024/01/10
現病歴: 頭痛、めまい
入院中の治療経過: 薬物療法を実施
備考: 経過良好"""

        result = parse_output_summary(input_text)

        assert result['入院期間'] == "2024/01/01～2024/01/10"
        assert result['現病歴'] == "頭痛、めまい"
        assert result['入院中の治療経過'] == "薬物療法を実施"
        assert result['備考'] == "経過良好"
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_multiline_section_content(self):
        """複数行のセクション内容テスト"""
        input_text = """入院期間: 2024/01/01～2024/01/10
現病歴: 頭痛
めまい
動悸
入院中の治療経過: 薬物療法を実施"""

        result = parse_output_summary(input_text)

        assert result['入院期間'] == "2024/01/01～2024/01/10"
        assert result['現病歴'] == "頭痛\nめまい\n動悸"
        assert result['入院中の治療経過'] == "薬物療法を実施"
    
    @patch('utils.text_processor.section_aliases', {"治療内容": "入院中の治療経過", "その他": "備考"})
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_section_aliases(self):
        """セクションエイリアスのテスト"""
        input_text = """入院期間: 2024/01/01～2024/01/10
現病歴: 頭痛
治療内容: 薬物療法
その他: 特記事項なし"""

        result = parse_output_summary(input_text)

        assert result['入院期間'] == "2024/01/01～2024/01/10"
        assert result['現病歴'] == "頭痛"
        assert result['入院中の治療経過'] == "薬物療法"  # 治療内容 → 入院中の治療経過
        assert result['備考'] == "特記事項なし"  # その他 → 備考
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_section_without_colon(self):
        """コロンなしのセクションテスト"""
        input_text = """入院期間 2024/01/01～2024/01/10
現病歴 頭痛、めまい
入院中の治療経過 薬物療法を実施"""

        result = parse_output_summary(input_text)

        assert result['入院期間'] == "2024/01/01～2024/01/10"
        assert result['現病歴'] == "頭痛、めまい"
        assert result['入院中の治療経過'] == "薬物療法を実施"
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_empty_sections(self):
        """空のセクションテスト"""
        input_text = """入院期間:
現病歴:  頭痛
入院中の治療経過:
備考: 特記事項なし"""

        result = parse_output_summary(input_text)

        assert result['入院期間'] == ""
        assert result['現病歴'] == "頭痛"
        assert result['入院中の治療経過'] == ""
        assert result['備考'] == "特記事項なし"
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_no_sections_found(self):
        """セクションが見つからない場合のテスト"""
        input_text = """これは普通のテキストです。
セクションの見出しは含まれていません。"""

        result = parse_output_summary(input_text)

        # すべてのセクションが空になることを確認
        assert all(value == "" for value in result.values())
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_empty_input(self):
        """空の入力テスト"""
        input_text = ""

        result = parse_output_summary(input_text)

        assert all(value == "" for value in result.values())
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_whitespace_handling(self):
        """空白文字の処理テスト"""
        input_text = """   入院期間:   2024/01/01～2024/01/10
        現病歴:  頭痛

        入院中の治療経過:    薬物療法    """

        result = parse_output_summary(input_text)

        assert result['入院期間'] == "2024/01/01～2024/01/10"
        assert result['現病歴'] == "頭痛"
        assert result['入院中の治療経過'] == "薬物療法"
    
    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ['入院期間', '現病歴', '入院時検査', '入院中の治療経過', '退院申し送り', '備考'])
    def test_duplicate_sections(self):
        """重複するセクションのテスト"""
        input_text = """入院期間: 2024/01/01～2024/01/10
現病歴: 頭痛
入院期間: 2024/02/01～2024/02/10
現病歴: 多尿"""

        result = parse_output_summary(input_text)

        # 最後に出現したセクションの内容が保持されることを確認
        assert result['入院期間'] == "2024/02/01～2024/02/10"
        assert result['現病歴'] == "多尿"


class TestSectionAliases:
    """section_aliasesの定数テスト"""

    def test_section_aliases_content(self):
        """セクションエイリアスの内容テスト"""
        expected_aliases = {
            "治療内容": "治療経過",
            "処方": "現在の処方",
            "薬剤": "現在の処方",
            "その他": "備考",
            "補足": "備考",
            "メモ": "備考",
            "病名": "主病名",
            "症状": "症状経過",
        }

        assert section_aliases == expected_aliases
    
    def test_aliases_are_strings(self):
        """エイリアスがすべて文字列であることのテスト"""
        for key, value in section_aliases.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
