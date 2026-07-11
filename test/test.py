import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from englishToKanaConverter import EnglishToKanaConverter


if __name__ == "__main__":
    c = EnglishToKanaConverter(True, os.path.join(os.path.dirname(__file__), "log.txt"))
    while True:
        try:
            text = input("文字列を入力（終了はCtrl+C）:")
            print(c.process(text))
        except (KeyboardInterrupt, EOFError):
            exit()
