import os

from englishToKanaConverter import EnglishToKanaConverter


if __name__ == "__main__":
    c = EnglishToKanaConverter(True)
    while True:
        try:
            text = input("文字列を入力（終了はCtrl+C）:")
            print(c.process(text))
        except (KeyboardInterrupt, EOFError):
            exit()
