import os

from englishToKanaConverter import EnglishToKanaConverter


if __name__ == "__main__":
    oldPath = os.path.join(os.path.dirname(__file__), "test.txt")
    newPath = os.path.join(os.path.dirname(__file__), "test_result.txt")
    while not os.path.exists(oldPath):
        print(f"このファイルと同じ場所に{os.path.basename(oldPath)}というファイルを作成し、変換したい内容を記入してください。\n準備ができたらEnterキーを押してください。")
        input()
    c = EnglishToKanaConverter(True)
    with open(oldPath, "r", encoding="utf-8") as f:
        text = f.read()
    result = c.process(text)
    with open(newPath, "w", encoding="utf-8") as f:
        f.write(result)
