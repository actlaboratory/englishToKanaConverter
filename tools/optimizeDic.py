import glob
import json
import os
import re
import sys

# englishToKanaConverter moduleのimportを可能にする
sys.path.append(os.getcwd())
from englishToKanaConverter.constants import ZENHAN_TABLE


def normalizeKey(key):
    if not key.isupper():
        print(f"{key}を大文字に変換しました。")
        key = key.upper()
    if re.search("[Ａ-Ｚ]", key):
        print(f"{key}に含まれる全角アルファベットを半角に変換しました。")
        key = key.translate(str.maketrans(ZENHAN_TABLE))
    if not re.match("^[A-Z']+$", key):
        sys.stderr.write(f"{key}には、半角大文字以外の文字が含まれています。\n")
    return key


def optimizeDictionary(path):
    with open(path, "r", encoding="utf-8") as f:
        oldData = json.load(f)
    newData = {}
    for key in sorted(oldData.keys(), key=str.lower):
        value = oldData[key]
        if not re.match("^[ァ-ヿ]+$", value):
            sys.stderr.write(f"変換先文字列{value}にカタカナ以外の文字が含まれています。\n")
        newData[normalizeKey(key)] = value
    print(f"登録単語数: {len(newData)}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(newData, f, ensure_ascii=False, indent=4)
        f.write("\n")


def optimizeWordList(path):
    with open(path, "r", encoding="utf-8") as f:
        oldData = json.load(f)
    newData = []
    seen = set()
    for item in oldData:
        item = normalizeKey(item)
        if item in seen:
            print(f"{item}は重複していたため除去しました。")
            continue
        seen.add(item)
        newData.append(item)
    newData.sort(key=str.lower)
    print(f"登録数: {len(newData)}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(newData, f, ensure_ascii=False, indent=4)
        f.write("\n")


if __name__ == "__main__":
    dictFiles = glob.glob(os.path.join("englishToKanaConverter", "dictionaries", "*.json"))
    for path in dictFiles:
        print(f"{os.path.basename(path)}を処理しています。")
        optimizeDictionary(path)
        print(f"{os.path.basename(path)}を保存しました。")

    listFiles = glob.glob(os.path.join("englishToKanaConverter", "constants", "*.json"))
    for path in listFiles:
        print(f"{os.path.basename(path)}を処理しています。")
        optimizeWordList(path)
        print(f"{os.path.basename(path)}を保存しました。")
