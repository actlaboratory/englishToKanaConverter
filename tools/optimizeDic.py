from fnmatch import translate
import glob
import json
import os
import re
import sys

# englishToKanaConverter moduleのimportを可能にする
sys.path.append(os.getcwd())
from englishToKanaConverter.englishToKanaConverter import ZENHAN_TABLE
from englishToKanaConverter import EnglishToKanaConverter


if __name__ == "__main__":
    files = glob.glob(os.path.join(
        "englishToKanaConverter", "dictionaries", "*.py"))
    for path in files:
        if os.path.basename(path) == "__init__.py":
            # 辞書本体ではない
            continue
        print(f"{os.path.basename(path)}を処理しています。")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        startIndex = text.find("{")
        prefix = text[:startIndex]
        # 最後のエントリの後の','を削除
        lastCommaIndex = text.rfind(",")
        if text[lastCommaIndex + 1:].strip().startswith("}"):
            text = text[:lastCommaIndex] + text[lastCommaIndex + 1:]
            print("最後のエントリの後の','を削除しました。")
        oldData = json.loads(text[startIndex:])
        newData = {}
        for key in sorted(oldData.keys(), key=str.lower):
            value = oldData[key]
            if not re.match("^[ァ-ヿ]+$", value):
                sys.stderr.write(f"変換先文字列{value}にカタカナ以外の文字が含まれています。\n")
            if not key.isupper():
                print(f"変換元文字列{key}を大文字に変換しました。")
                key = key.upper()
            if re.search("[Ａ-Ｚ]", key):
                print(f"変換元文字列{key}に含まれる全角アルファベットを半角に変換しました。")
                key = key.translate(str.maketrans(ZENHAN_TABLE))
            if not re.match("^[A-Z']+$", key):
                sys.stderr.write(f"変換元文字列{key}には、半角大文字以外の文字が含まれています。\n")
            newData[key] = value
        print(f"登録単語数: {len(newData)}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(prefix)
            f.write(json.dumps(newData, ensure_ascii=False, indent="    "))
            f.write("\n")
        print(f"{os.path.basename(path)}を保存しました。")
