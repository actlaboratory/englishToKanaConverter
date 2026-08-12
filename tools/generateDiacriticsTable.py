import json
import os
import unicodedata

# アクセント記号付きラテン文字が含まれるUnicodeブロック（Blocks.txtで定義される公式の範囲）
LATIN_BLOCKS = (
    (0x0080, 0x00FF),  # Latin-1 Supplement
    (0x0100, 0x017F),  # Latin Extended-A
    (0x0180, 0x024F),  # Latin Extended-B
    (0x1E00, 0x1EFF),  # Latin Extended Additional
)

OUTPUT_PATH = os.path.join("englishToKanaConverter", "constants", "diacritics.json")


def buildTable():
    table = {}
    for start, end in LATIN_BLOCKS:
        for codepoint in range(start, end + 1):
            char = chr(codepoint)
            if not char.isalpha():
                continue
            # Unicodeの正規分解（NFKD）を行い、結合文字（アクセント記号）を取り除く。
            # 例: "í"（U+00ED）-> "i" + COMBINING ACUTE ACCENT -> "i"
            decomposed = unicodedata.normalize("NFKD", char)
            stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
            if not stripped or stripped == char:
                # 分解できなかった文字（ß, æ, øなど）は対象外
                continue
            if not all(ord(c) < 128 for c in stripped):
                # 分解結果がASCIIに収まらない場合は対象外
                continue
            table[char] = stripped
    return {key: table[key] for key in sorted(table, key=ord)}


if __name__ == "__main__":
    table = buildTable()
    print(f"生成件数: {len(table)}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"{OUTPUT_PATH}を更新しました。")
