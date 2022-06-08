import json
import logging
import os
import re
import traceback

from .dictionaries import *


# 大文字が連続する際にそれぞれを独立した単語として扱う最大数
UPPER_MAX = 3


class EnglishToKanaConverter:
    def __init__(self, debug=False) -> None:
        # デバッグ用のログ出力
        if debug:
            logHandler = logging.FileHandler(f"{os.path.splitext(__file__)[0]}.log", "w", "utf-8")
        else:
            logHandler = logging.NullHandler()
        logHandler.setLevel(logging.DEBUG)
        self.log = logging.getLogger(__class__.__name__)
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(logHandler)
        # 辞書準備
        self._words = WORDS
        self._phrases = PHRASES
        self._tails = SUFFIX
        self._spell = SPELL
        self._zenhan = ZENHAN
        self.log.info("ready!")

    def _zenToHan(self, s: str) -> str:
        self.log.debug("zenToHan")
        self.log.debug(f"in: {s}")
        s = s.translate(str.maketrans(self._zenhan))
        self.log.debug(f"out: {s}")
        return s

    def _splitUpperCase(self, s: str) -> str:
        self.log.debug("splitUpperCase")
        self.log.debug(f"in: {s}")
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
            if length > UPPER_MAX:
                # 一定以上長い大文字列は無視
                self.log.debug("skipped")
                continue
            for cnt in range(match.end(1) - 1, match.start(1) - 1, -1):
                self.log.debug(f"found: {s[s.rfind(' ', 0, cnt) + 1:cnt]}{s[cnt:s.find(' ', cnt)]}")
                s = s[:cnt] + " " + s[cnt:]
                self.log.debug(f"converted: {s[s.rfind(' ', 0, cnt) + 1:cnt]}{s[cnt:s.find(' ', cnt + 1)]}")
        self.log.debug(f"out: {s}")
        return s

    def _engToKana(self, s: str) -> str:
        self.log.debug("engToKana")
        self.log.debug(f"in: {s}")
        # 英語がカナになった結果の格納用
        result = ""
        while len(s) > 0:
            self.log.debug(f"processing: {s}")
            match = re.search("[a-zA-Z]+", s)
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
            val = self._words.get(match.group().upper())
            if val is not None:
                # 変換できた
                self.log.debug(f"whole converted: {match.group()} -> {val}")
                result += val
                s = s[match.end():]
                continue
            # 複合語や接尾語も考慮しつつ変換する
            self.log.debug("check started")
            # 変換できない単語が出てきたらTrue
            failedFlag = False
            # カナを一時保存
            tmpKana = ""
            # 変換できた文字はtmpEngから削除していく
            while len(tmpEng) > 0:
                # 文字数を1文字ずつ減らしながら辞書の単語と合致するものを探す
                for cnt in range(len(tmpEng), 0, -1):
                    self.log.debug(f"checking: {tmpEng[:cnt]}")
                    val = self._phrases.get(tmpEng.upper()[:cnt])
                    if val is not None:
                        # 変換できた
                        self.log.debug(f"found: {tmpEng[:cnt]} -> {val}")
                        tmpKana += val
                        tmpEng = tmpEng[cnt:]
                        self.log.debug(f"current kana: {tmpKana}, current eng: {tmpEng}")
                        # 接尾語の確認
                        for tail in self._tails:
                            if tmpEng.upper().startswith(tail):
                                # 接尾語が見つかった
                                self.log.debug(f"tail {tail} found")
                                tmpKana += self._tails[tail]
                                tmpEng = tmpEng[len(tail):]
                                self.log.debug(f"current kana: {tmpKana}, current eng: {tmpEng}")
                                # これ以上見なくて良い
                                break
                        # これ以上文字数を減らしてみる必要はない
                        break
                if val is None:
                    # 変換に失敗した
                    self.log.debug(f"failed: {tmpEng}")
                    failedFlag = True
                    break
            if failedFlag:
                # 変換できなかったため英語のまま
                self.log.debug(f"not converted: {match.group()}")
                result += match.group()
                s = s[match.end():]
            else:
                # 変換できた
                self.log.debug(f"result: {match.group()} -> {tmpKana}")
                result += tmpKana
                s = s[match.end():]
        self.log.debug(f"out: {result}")
        return result

    def _romanToKana(self, s: str) -> str:
        self.log.debug("romanToKana")
        return s

    def _trimWhitespaceBetweenUpperCase(self, s: str) -> str:
        self.log.debug("trimWhitespaceBetweenUpperCase")
        self.log.debug(f"in: {s}")
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
        self.log.debug(f"out: {s}")
        return s

    def _alphaToSpell(self, s: str) -> str:
        self.log.debug("alphaToSpell")
        self.log.debug(f"in: {s}")
        # アルファベットを探す
        self.log.debug("searching for alphabets")
        result = re.finditer("[a-zA-Z]", s)
        result = list(result)
        # 文字の挿入時にインデックスが狂わないように後ろから処理する
        result.reverse()
        for match in result:
            char = match.group()
            self.log.debug(f"found: {char}")
            kana = self._spell.get(char.upper())
            if kana is None:
                self.log.error(f"unknown character: {char}")
            self.log.debug(f"converted: {char} -> {kana}")
            s = s[:match.start()] + kana + s[match.end():]
        self.log.debug(f"out: {s}")
        return s

    def process(self, s: str) -> str:
        s = self._zenToHan(s)
        s = self._splitUpperCase(s)
        s = self._engToKana(s)
        s = self._romanToKana(s)
        s = self._trimWhitespaceBetweenUpperCase(s)
        s = self._alphaToSpell(s)
        return s
