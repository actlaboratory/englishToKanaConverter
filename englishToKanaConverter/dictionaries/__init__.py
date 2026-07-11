# 辞書データ

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
