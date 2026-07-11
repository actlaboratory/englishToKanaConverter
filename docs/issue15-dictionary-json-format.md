# Issue #15 対応仕様書: 辞書データのJSON化

## 1. 背景・目的

現在、`englishToKanaConverter/dictionaries`ディレクトリ内の辞書データ、および`constants.py`内の一部の定数は、Pythonのソースコード（`.py`ファイル内の辞書・タプルリテラル）として管理されている。

これらは実質的にはデータであり、プログラムロジックを含まない。しかし`.py`ファイルとして管理されているため、

* テキストエディタ以外の汎用ツール（JSONバリデータ、他言語からの読み込み、Web上のJSONエディタ等）を活用しにくい
* Pythonの構文（クォート、末尾カンマの扱いなど）を意識する必要があり、辞書メンテナンス時に誤って構文を壊すリスクがある
* データとロジックが分離されておらず、将来的な辞書管理の自動化（外部ツールとの連携等）がしにくい

といった保守上の課題がある。Issue #15はこれを解消するため、辞書データをPythonから切り離しJSON形式で格納することを求めている。

## 2. スコープ

### 2.1 対象

* `englishToKanaConverter/dictionaries/`配下の辞書データファイル（6ファイル）
  * `phrases.py` → `phrases.json`
  * `prefix.py` → `prefix.json`
  * `roman.py` → `roman.json`
  * `spell.py` → `spell.json`
  * `suffix.py` → `suffix.json`
  * `words.py` → `words.json`
* `englishToKanaConverter/constants.py`内の以下2定数
  * `UPPER_IGNORE`（読み下しが必要な大文字列のタプル）
  * `MUST_SPELLED`（必ずスペルアウトしなければならない文字列のタプル）
* 上記データの読み込み方法（`dictionaries/__init__.py`、`constants.py`）
* `tools/optimizeDic.py`（辞書最適化ツール）の改修
* `README.md`「辞書のメンテナンス」節の記述更新

### 2.2 対象外（現状維持）

* `constants.py`内の上記2定数以外のもの（`UPPER_MAX`、`ROMAN_MIN`、`SOKUON_IGNORE`、`ZENHAN_TABLE`）
  * Issue本文で名指しされているのは`UPPER_IGNORE`と`MUST_SPELLED`のみであり、他の定数は単純な値やロジックに近いテーブルであるため、Pythonのまま残す。
* `englishToKanaConverter.py`の変換アルゴリズム自体
* `tools/checkHISSDic.py`の処理内容（辞書の参照方法が変わらない限り改修不要）
* 公開API（`EnglishToKanaConverter.process()`等）の入出力仕様

## 3. 現状の仕様（as-is）

### 3.1 辞書データファイルの形式

各ファイルは、先頭にコメント（用途説明）、続けて`変数名 = { ... }`という形式のPython辞書リテラルを持つ。

```python
# 接尾語
SUFFIX = {
    "'S": "ズ",
    "D": "ドゥ",
    ...
}
```

キーは半角大文字アルファベット＋アポストロフィーのみ、値は全角カタカナのみという制約がある（README.mdに明記済み）。

現在の各ファイルのエントリ数は以下の通り（参考値）。

| ファイル | エントリ数 |
| --- | --- |
| phrases.py | 48,975 |
| words.py | 655 |
| roman.py | 179 |
| spell.py | 26 |
| suffix.py | 8 |
| prefix.py | 2 |

`phrases.py`は約1.9MBあり、他と比べて突出して大きい。

### 3.2 ロード方法

`dictionaries/__init__.py`が各サブモジュールから辞書オブジェクトをインポートし、パッケージの名前空間に公開している。

```python
from .phrases import PHRASES
from .prefix import PREFIX
from .roman import ROMAN
from .spell import SPELL
from .suffix import SUFFIX
from .words import WORDS
```

`englishToKanaConverter.py`側は`from . import dictionaries`した上で、`dictionaries.WORDS.get(...)`のように属性アクセスで参照している（`_engToKana`、`_partsToKana`、`_romanToKana`、`_alphaToSpell`の各メソッド）。

### 3.3 `constants.py`の`UPPER_IGNORE`・`MUST_SPELLED`

`constants.py`ではタプルリテラルとして定義されており、`englishToKanaConverter.py`側は`from .constants import *`によりモジュール名前空間に取り込んだ上で、`in`演算子によるメンバーシップ判定にのみ使用している（`_splitUpperCase`、`_partsToKana`）。値の書き換えや順序への依存はない。

### 3.4 `tools/optimizeDic.py`の処理内容

現状の`optimizeDic.py`は、`dictionaries/*.py`をテキストとして読み込み、

1. 最初の`{`より前（`# コメント` + `変数名 = `）を`prefix`として保持
2. 末尾のエントリの後ろに末尾カンマがあれば除去（Pythonの辞書リテラルはJSONと異なり末尾カンマを許容するため）
3. `{`以降を`json.loads`でパース（＝キーが常にダブルクォートの文字列であるため、実質的にJSON互換）
4. キーを`str.lower`基準でソート
5. 値がカタカナのみか、キーが半角大文字＋アポストロフィーのみかを検証し、違反時は標準エラー出力に警告
6. キーが小文字を含む場合は大文字化、全角アルファベットを含む場合は半角化（`ZENHAN_TABLE`を利用）
7. `prefix + json.dumps(newData, ensure_ascii=False, indent="    ")`の形でファイルに書き戻す

つまり、**現状の辞書データファイルは中身がすでにJSON互換のテキストであり**、`optimizeDic.py`は実質的に「Pythonの変数宣言でラップされたJSON」を編集するツールとして動作している。JSON化はこのラッパー部分（コメント・変数宣言・末尾カンマ許容）を取り除く作業に相当する。

### 3.5 `tools/checkHISSDic.py`との関係

HISSの読み辞書と本モジュールの変換結果を突き合わせ、変換できない単語を`failed.txt`に出力するツール。`EnglishToKanaConverter`のpublic API（`process()`）のみを使用しており、辞書データの内部形式には依存していない。JSON化による影響はない。

## 4. 要件

### 4.1 機能要件

* F1: `dictionaries`配下の6辞書データをJSONファイルとして格納する。
* F2: `constants.py`の`UPPER_IGNORE`・`MUST_SPELLED`を、それぞれ独立したJSONファイルとして格納する。
* F3: JSON化後も、`dictionaries.PHRASES`・`dictionaries.WORDS`・`dictionaries.PREFIX`・`dictionaries.SUFFIX`・`dictionaries.ROMAN`・`dictionaries.SPELL`、および`UPPER_IGNORE`・`MUST_SPELLED`は、既存コードから見て**現在と同じ型・同じ内容でアクセスできる**（`englishToKanaConverter.py`に修正が不要、または最小限の修正で済む）こと。
* F4: `optimizeDic.py`をJSONファイルに対応させ、現状と同等の最適化（ソート・大文字化・全角半角変換・キー/値のバリデーション）を行えるようにする。対象は辞書データ6ファイルに加え、`constants/upper_ignore.json`・`constants/must_spelled.json`も含む。
* F5: `README.md`の「辞書のメンテナンス」節を、JSON編集を前提にした説明に更新する。

### 4.2 互換性要件

* C1: 変換結果（`EnglishToKanaConverter.process()`の出力）はJSON化の前後で一切変化しないこと（データの内容は移動のみで変更しない）。
* C2: `sample.py`・`tools/checkHISSDic.py`など、辞書データを直接importしていない既存ツールは無改修で動作すること。

### 4.3 非機能要件

* N1: JSONの文字コードはUTF-8固定とする（現行のPythonファイルと同じ）。
* N2: `phrases.json`は約2MB・5万エントリ規模になる見込み。`json.load`はC実装のため、`import`によるPythonリテラル評価と比べて起動時間に大きな悪化は想定されないが、実装時に簡易的な計測を行い許容範囲であることを確認する。
* N3: JSON構文エラーがあった場合、モジュールのimport時に分かりやすい形で失敗すること（現状も構文エラーがあればPythonのSyntaxErrorで失敗するため、同等の位置づけで良い＝特別なエラーハンドリングの追加は不要）。

## 5. 対応方針（to-be仕様）

### 5.1 ファイル構成案

`UPPER_IGNORE`・`MUST_SPELLED`は、1つの`constants.json`にまとめるのではなく、`constants`という専用ディレクトリを設けた上で、それぞれ独立したJSONファイル（`upper_ignore.json`・`must_spelled.json`）として配置する。

```
englishToKanaConverter/
├── constants.py             # UPPER_IGNORE, MUST_SPELLED以外の定数はそのまま残す。
│                             # UPPER_IGNORE/MUST_SPELLEDはconstants/配下のJSONを読み込んで公開する
├── constants/                # 新規: 単語リスト系の定数をJSONで格納する専用ディレクトリ
│   ├── upper_ignore.json      # 新規（UPPER_IGNOREを格納）
│   └── must_spelled.json      # 新規（MUST_SPELLEDを格納）
└── dictionaries/
    ├── __init__.py            # JSONを読み込むローダーに書き換え
    ├── phrases.json            # 新規（phrases.pyを置き換え）
    ├── prefix.json
    ├── roman.json
    ├── spell.json
    ├── suffix.json
    └── words.json
```

`dictionaries/*.py`・`constants.py`内の該当定義は削除し、上記JSONファイルに置き換える。`dictionaries`ディレクトリとは別に`constants`ディレクトリを設けるのは、両者が意味的に異なるため（`dictionaries`は「英単語→カナ」の変換マッピング、`constants`は変換ルールに使う単語のリストであり、キー・値の構造もバリデーション規則も異なる）。

### 5.2 JSONファイルのフォーマット

**辞書データ（phrases/prefix/roman/spell/suffix/words）**

トップレベルが単純なオブジェクト（`{"KEY": "値", ...}`）のみのJSON。キー・値の制約（キーは半角大文字＋アポストロフィーのみ、値は全角カタカナのみ）は現状を踏襲する。

```json
{
    "ABASH": "アバッシュ",
    "ABASHED": "アバッシュトゥ"
}
```

**`constants/upper_ignore.json`・`constants/must_spelled.json`**

それぞれ単一のリストのみを持つファイルなので、トップレベルはJSON配列とする（辞書データと違いキーを持たない）。

```json
[
    "AND",
    "ARM",
    "BES",
    "..."
]
```

いずれもJSONにはコメントを書けないため、各ファイル冒頭にあった用途コメント（例:「単体でも、他の単語との組み合わせでも良いもの」）は失われる。この情報はREADME.mdの「辞書ファイルの種類」一覧（既存）に一本化し、JSON側では持たない方針とする。

### 5.3 ロード処理の変更

**`dictionaries/__init__.py`**

現状のサブモジュールimportをやめ、パッケージディレクトリ基準でJSONファイルを読み込み、モジュール変数として公開する形に変更する。

```python
import json
import os

_DIR = os.path.dirname(__file__)

def _load(name):
    with open(os.path.join(_DIR, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)

PHRASES = _load("phrases")
PREFIX = _load("prefix")
ROMAN = _load("roman")
SPELL = _load("spell")
SUFFIX = _load("suffix")
WORDS = _load("words")
```

**`constants.py`**

`UPPER_IGNORE`・`MUST_SPELLED`の定義部分を、`constants/`ディレクトリ配下のJSON読み込み＋タプル変換に置き換える（呼び出し側は`in`判定のみのためlistでも動作するが、元がタプル＝イミュータブルであった点を踏襲し`tuple()`でラップする）。

```python
import json
import os

_CONST_DIR = os.path.join(os.path.dirname(__file__), "constants")

def _loadList(name):
    with open(os.path.join(_CONST_DIR, f"{name}.json"), encoding="utf-8") as f:
        return tuple(json.load(f))

UPPER_IGNORE = _loadList("upper_ignore")
MUST_SPELLED = _loadList("must_spelled")
```

他の定数（`UPPER_MAX`等）はこのファイル内にPythonの値としてそのまま残す。呼び出し側（`englishToKanaConverter.py`の`from .constants import *`）は変更不要。

### 5.4 `optimizeDic.py`の改修方針

`optimizeDic.py`は、構造の異なる2種類のJSONファイル群を扱うことになるため、それぞれ別ルートで処理する。

**辞書データ（`dictionaries/*.json`）**

* 走査対象を`dictionaries/*.py`から`dictionaries/*.json`に変更する。
* 現状の「先頭の`{`を探す」「末尾カンマを除去する」といったPythonリテラル対応のテキスト処理は不要になり、`json.load`・`json.dump`（またはdumpsして書き込み）に置き換えられる。
* キー・値のバリデーション（大文字化、全角→半角変換、カタカナ/半角大文字チェック）、キーのソート（`str.lower`基準）は現行ロジックを踏襲する。

**単語リスト（`constants/*.json`）**

* `constants/upper_ignore.json`・`constants/must_spelled.json`も最適化対象に含める。トップレベルがJSON配列であり、辞書データ（オブジェクト）とは構造が異なるため、専用の処理を追加する。
  * 各要素について、辞書データのキーと同じ規則（大文字化、全角→半角変換、`^[A-Z']+$`に合致するかの検証）を適用する。
  * 配列内の重複要素を除去する（現行の`UPPER_IGNORE`に`"AND"`の重複があることが判明しており、この処理で自動的に解消される）。
  * 配列を`str.lower`基準でソートする（辞書データのキーソートと同じ考え方）。
  * カタカナ値の妥当性チェックは対象外（値を持たないリストのため）。

### 5.5 ドキュメント更新

`README.md`の「辞書の最適化」「辞書への単語登録時の注意点」節を、「`.py`を編集する」という記述から「`.json`を編集する」という記述に更新する。制約（キー・値のルール）自体は変わらないため、ルールの内容は変更不要。

## 6. 移行手順（想定ステップ）

1. `dictionaries/*.py`の辞書オブジェクト部分（コメント・変数宣言を除いた`{...}`）をそのまま`dictionaries/*.json`として書き出す。
2. `constants.py`から`UPPER_IGNORE`・`MUST_SPELLED`を、新設する`constants/`ディレクトリ配下の`upper_ignore.json`・`must_spelled.json`（JSON配列）に切り出す。
3. `dictionaries/__init__.py`をJSONローダー方式に書き換える。
4. `constants.py`を、`constants/`配下のJSON読み込み＋残りの定数定義という構成に書き換える。
5. `dictionaries/*.py`・（`constants.py`内の該当箇所）を削除する。
6. `tools/optimizeDic.py`をJSON対応に改修する（辞書データ6ファイル＋`constants/*.json`の両方を最適化対象にする）。
7. `python tools/optimizeDic.py`を実行し、全ファイル（`constants/*.json`含む）が警告なく処理でき、かつ`UPPER_IGNORE`の`"AND"`重複が解消されることを確認する。
8. `python sample.py`および`tools/checkHISSDic.py`で変換結果に差分が出ないことを確認する（移行前後でのサンプル入力に対する出力比較を推奨）。
9. `README.md`を更新する。

## 7. 未決事項・検討事項

* **既知のデータ不整合**: 調査中、現行の`UPPER_IGNORE`タプルに`"AND"`が2回登場している（`constants.py`内の重複）ことを確認した。5.4節の方針により、`optimizeDic.py`が`constants/*.json`を最適化対象に含め重複除去を行うため、移行後の初回最適化実行時に自動的に解消される。

## 8. 影響ファイル一覧（実装時の変更対象）

| ファイル | 変更内容 |
| --- | --- |
| `englishToKanaConverter/dictionaries/phrases.py` | 削除（→`phrases.json`新規作成） |
| `englishToKanaConverter/dictionaries/prefix.py` | 削除（→`prefix.json`新規作成） |
| `englishToKanaConverter/dictionaries/roman.py` | 削除（→`roman.json`新規作成） |
| `englishToKanaConverter/dictionaries/spell.py` | 削除（→`spell.json`新規作成） |
| `englishToKanaConverter/dictionaries/suffix.py` | 削除（→`suffix.json`新規作成） |
| `englishToKanaConverter/dictionaries/words.py` | 削除（→`words.json`新規作成） |
| `englishToKanaConverter/dictionaries/__init__.py` | JSONローダーに書き換え |
| `englishToKanaConverter/constants.py` | `UPPER_IGNORE`・`MUST_SPELLED`をJSON読み込みに変更 |
| `englishToKanaConverter/constants/upper_ignore.json` | 新規作成 |
| `englishToKanaConverter/constants/must_spelled.json` | 新規作成 |
| `tools/optimizeDic.py` | JSON対応に改修（`dictionaries/*.json`・`constants/*.json`の両方に対応） |
| `README.md` | 辞書メンテナンス節の記述更新 |

`tools/checkHISSDic.py`・`sample.py`・`englishToKanaConverter/englishToKanaConverter.py`は変更不要（F3の互換性要件を満たす限り）。
