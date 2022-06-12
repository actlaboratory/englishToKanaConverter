import glob
import json
import os
import re


if __name__ == "__main__":
    files = glob.glob(os.path.join("englishToKanaConverter", "dictionaries", "*.py"))
    for path in files:
        if os.path.basename(path) == "__init__.py":
            # 辞書本体ではない
            continue
        print(f"{os.path.basename(path)}を処理しています。")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        startIndex = text.find("{")
        prefix = text[:startIndex]
        oldData = json.loads(text[startIndex:])
        newData = {}
        for key in sorted(oldData.keys()):
            value = oldData[key]
            if not re.match("^[ァ-ヿ]+$", value):
                print(f"変換先文字列にカタカナ以外の文字が含まれています。。対象文字列:{value}")
            if not key.isupper():
                print(f"変換元文字列{key}を大文字に変換しました。")
                key = key.upper()
            if not re.match("^[A-Z']+$", key):
                print(f"変換元文字列{key}には、半角大文字以外の文字が含まれています。")
            newData[key] = value
        with open(path, "w", encoding="utf-8") as f:
            f.write(prefix)
            f.write(json.dumps(newData, ensure_ascii=False, indent="    "))
            f.write("\n")
