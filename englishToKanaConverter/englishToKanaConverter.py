import json
import logging
import os
import re
import traceback
from typing import Tuple

from . import dictionaries
from .constants import *


class EnglishToKanaConverter:
    def __init__(self, debug=False) -> None:
        # デバッグ用のログ出力
        self.log = logging.getLogger(__class__.__name__)
        if debug:
            logHandler = logging.FileHandler(f"{os.path.splitext(__file__)[0]}.log", "w", "utf-8")
            logHandler.setLevel(logging.DEBUG)
            self.log.setLevel(logging.DEBUG)
        else:
            logHandler = logging.NullHandler()
            logHandler.setLevel(logging.CRITICAL)
            self.log.setLevel(logging.CRITICAL)
        self.log.addHandler(logHandler)

    def _zenToHan(self, s: str) -> str:
        self.log.debug(f"zenToHan in: {s}")
        s = s.translate(str.maketrans(ZENHAN_TABLE))
        self.log.debug(f"zenToHan out: {s}")
        return s

    def _splitUpperCase(self, s: str) -> str:
        self.log.debug(f"splitUpperCase in: {s}")
        self.log.debug("searching for upper case")
        # 大文字を探す
        result = re.finditer("[^A-Z]?([A-Z]+)", s)
        result = list(result)
        # 文字の挿入時にインデックスが狂わないように後ろから処理する
        result.reverse()
        for match in result:
            self.log.debug(f"match: {match.group(1)}")
            length = match.end(1) - match.start(1)
            self.log.debug(f"length: {length}")
            if length > UPPER_MAX or match.group(1) in UPPER_IGNORE:
                # 一定以上長い大文字列や、特定の大文字列は無視
                self.log.debug("skipped")
                continue
            for cnt in range(match.end(1) - 1, match.start(1) - 1, -1):
                self.log.debug(f"found: {s[s.rfind(' ', 0, cnt) + 1:cnt]}{s[cnt:s.find(' ', cnt)]}")
                s = s[:cnt] + " " + s[cnt:]
                self.log.debug(f"converted: {s[s.rfind(' ', 0, cnt) + 1:cnt]}{s[cnt:s.find(' ', cnt + 1)]}")
        self.log.debug(f"splitUpperCase out: {s}")
        return s

    def _engToKana(self, s: str) -> str:
        self.log.debug(f"engToKana in: {s}")
        # 英語がカナになった結果の格納用
        result = ""
        while len(s) > 0:
            match = re.search("[a-zA-Z']+", s)
            if match is None:
                # 残りは日本語か記号
                result += s
                break
            # 英語が出てくるまででは処理不要
            result += s[:match.start()]
            self.log.debug(f"match: {match.group()}")
            # 英語を一時保存
            tmpEng = match.group()
            # 単独で存在すべき文字列と合致するか
            val = dictionaries.WORDS.get(match.group().upper())
            if val is not None:
                # 変換できた
                self.log.debug(f"whole converted: {match.group()} -> {val}")
                result += val
                s = s[match.end():]
                continue
            # 複合語や接尾語も考慮しつつ変換する
            success, converted, remaining = self._partsToKana(match.group())
            result += converted
            s = s[match.end():]
        self.log.debug(f"engToKana out: {result}")
        return result

    def _partsToKana(self, s: str) -> Tuple[bool, str, str]:
        self.log.debug(f"partsToKana in: {s}")
        # 変数の初期化
        success = False
        converted = ""
        remaining = ""
        # 文字数を減らしながら変換できそうな単語を探す
        for cnt in range(len(s), 0, -1):
            tmp = s[0:cnt]
            self.log.debug(f"checking: {tmp}")
            converted = dictionaries.PHRASES.get(tmp.upper(), "")
            if converted == "":
                # 変換できなかった
                self.log.debug(f"not found: {tmp}")
                success = False
                continue
            success = True
            self.log.debug(f"found: {tmp} -> {converted}")
            remaining = s[cnt:]
            if remaining == "":
                self.log.debug(f"partsToKana out: success={success}, converted={converted}, remaining={remaining}")
                return success, converted, remaining
            # 接尾語の確認
            suffix = dictionaries.SUFFIX.get(remaining.upper(), "")
            if suffix:
                # 接尾語が見つかった
                self.log.debug(f"suffix {remaining} -> {suffix}")
                converted += suffix
                self.log.debug(f"partsToKana out: success={success}, converted={converted}, remaining={''}")
                return success, converted, ""
            # 続きをチェック
            success2, converted2, remaining2 = self._partsToKana(remaining)
            if not success2:
                # 変換できなかった
                success = False
                continue
            self.log.debug(f"partsToKana out: success={success}, converted={converted + converted2}, remaining={remaining2}")
            return success, converted + converted2, remaining2
        # すべて変換できなかった
        success = False
        converted = s
        remaining = ""
        self.log.debug(f"partsToKana out: success={success}, converted={converted}, remaining={remaining}")
        return success, converted, remaining

    def _romanToKana(self, s: str) -> str:
        self.log.debug(f"romanToKana in: {s}")
        # 結果の格納用
        result = ""
        while len(s) > 0:
            match = re.search("[a-zA-Z]+", s)
            if match is None:
                # 残りは日本語か記号
                result += s
                break
            # 英語が出てくるまででは処理不要
            result += s[:match.start()]
            self.log.debug(f"match: {match.group()}")
            # 変換元の文字列（辞書と合わせるためにすべて大文字）
            word = match.group().upper()
            if len(word) < ROMAN_MIN:
                # 短い単語は変換しない
                self.log.debug(f"skipped: {match.group()}")
                result += match.group()
                s = s[match.end():]
                continue
            # 変換結果の一時保存用
            tmpResult = ""
            index = 0
            while index != len(word):
                # 促音の判定
                # 次に文字があれば
                if index != len(word) - 1:
                    phrase = word[index:index + 2]
                    if phrase[0] == phrase[1] and phrase[0] not in SOKUON_IGNORE:
                        # 促音が見つかった
                        self.log.debug(f"sokuon {phrase} found")
                        tmpResult += "ッ"
                        self.log.debug(f"tmpResult: {tmpResult}")
                        index += 1
                        continue
                found = dictionaries.ROMAN.get(word[index], "")
                if found != "":
                    self.log.debug(f"found: {word[index]} -> {found}")
                    # 最後の文字ならば
                    if index == len(word) - 1:
                        tmpResult += found
                        index = len(word)
                        continue
                    nextIndex = index
                    for i in range(index + 2, len(word) + 1):
                        self.log.debug(f"searching for: {word[index: i]}")
                        newFound = dictionaries.ROMAN.get(word[index: i], "")
                        if newFound == "":
                            self.log.debug(f"not found: {word[index: i]}")
                            nextIndex = i - 1
                            break
                        self.log.debug(f"found: {word[index: i]} -> {newFound}")
                        nextIndex = i
                        found = newFound
                    index = nextIndex
                    tmpResult += found
                    continue
                else:
                    foundFlag = False
                    for i in range(len(word), index + 1, -1):
                        self.log.debug(f"searching for: {word[index: i]}")
                        newFound = dictionaries.ROMAN.get(word[index:i], "")
                        if newFound != "":
                            self.log.debug(f"found: {word[index: i]} -> {newFound}")
                            foundFlag = True
                            index = i
                            tmpResult += newFound
                            break
                    if not foundFlag:
                        # 変換できなかった
                        tmpResult = match.group()
                        break
            result += tmpResult
            s = s[match.end():]
        self.log.debug(f"romanToKana out: {result}")
        return result

    def _trimWhitespaceBetweenUpperCase(self, s: str) -> str:
        self.log.debug(f"trimWhitespaceBetweenUpperCase in: {s}")
        self.log.debug("searching for upper case")
        # 大文字を探す
        result = re.finditer("[A-Z]+", s)
        result = list(result)
        # 文字の挿入時にインデックスが狂わないように後ろから処理する
        result.reverse()
        for match in result:
            self.log.debug(f"match: {match.group()}")
            length = match.end() - match.start()
            self.log.debug(f"length: {length}")
            if length > 1:
                # 連続する大文字は無視
                self.log.debug("skipped")
                continue
            index = match.start()
            if index > 0 and s[index - 1] == " ":
                self.log.debug(f"found: {s[s.rfind(' ', 0, index) + 1:index]}{s[index:s.find(' ', index)]}")
                s = s[:index - 1] + s[index:]
                self.log.debug(f"converted: {s[s.rfind(' ', 0, index) + 1:index]}{s[index:s.find(' ', index)]}")
        self.log.debug(f"trimWhitespaceBetweenUpperCase out: {s}")
        return s

    def _alphaToSpell(self, s: str) -> str:
        self.log.debug(f"alphaToSpell in: {s}")
        # アルファベットを探す
        self.log.debug("searching for alphabets")
        result = re.finditer("[a-zA-Z]", s)
        result = list(result)
        # 文字の挿入時にインデックスが狂わないように後ろから処理する
        result.reverse()
        for match in result:
            char = match.group()
            self.log.debug(f"found: {char}")
            kana = dictionaries.SPELL.get(char.upper())
            if kana is None:
                self.log.error(f"unknown character: {char}")
            self.log.debug(f"converted: {char} -> {kana}")
            s = s[:match.start()] + kana + s[match.end():]
        self.log.debug(f"alphaToSpell out: {s}")
        return s

    def process(self, s: str, spellout: bool = True) -> str:
        self.log.debug(f"process in: {s}")
        s = self._zenToHan(s)
        s = self._splitUpperCase(s)
        s = self._engToKana(s)
        s = self._romanToKana(s)
        s = self._trimWhitespaceBetweenUpperCase(s)
        if spellout:
            s = self._alphaToSpell(s)
        self.log.debug(f"process out: {s}")
        return s
