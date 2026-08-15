from enum import Enum


class ConversionMode(Enum):
    """変換モード"""

    # 標準（読めなかったアルファベットはスペルアウトする）
    STANDARD = 0
    # 読めない単語を英語のまま残す（辞書のメンテナンス用）
    KEEP_UNREADABLE = 1
    # すべての単語を強制的にスペルアウトする（文字と文字の間に区切り文字を挿入する）
    SPELL_ALL = 2
