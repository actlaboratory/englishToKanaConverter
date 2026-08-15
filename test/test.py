import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from englishToKanaConverter import ConversionMode, EnglishToKanaConverter


# 番号で選択できる変換モードの一覧
MODES = (
    (ConversionMode.STANDARD, "標準"),
    (ConversionMode.KEEP_UNREADABLE, "読めない単語を英語のまま残す"),
    (ConversionMode.SPELL_ALL, "すべての単語をスペルアウトする"),
)


if __name__ == "__main__":
    c = EnglishToKanaConverter(True, os.path.join(os.path.dirname(__file__), "log.txt"))
    mode, modeName = MODES[0]
    print("変換モード:")
    for i, (_, name) in enumerate(MODES, 1):
        print(f"    {i}: {name}")
    print("数字のみを入力すると、そのモードに切り替わります。")
    print(f"現在のモード: {modeName}")
    while True:
        try:
            text = input("文字列を入力（終了はCtrl+C）:")
            if text.isdecimal() and 1 <= int(text) <= len(MODES):
                # モードの切り替え
                mode, modeName = MODES[int(text) - 1]
                print(f"現在のモード: {modeName}")
                continue
            print(c.process(text, mode))
        except (KeyboardInterrupt, EOFError):
            exit()
