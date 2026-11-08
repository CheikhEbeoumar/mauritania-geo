from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Generic, Iterable, List, Optional, TypeVar

from .model import COMMUNES as _COMMUNES
from .model import MOUGHATAAS as _MOUGHATAAS
from .model import WILAYAS as _WILAYAS

_ARABIC_DIACRITICS = dict.fromkeys(
    list(range(0x064B, 0x0653)) + [0x0670, 0x0640] + list(range(0x06D6, 0x06EE))
)

ARABIC_LETTER_FOLDS = {
    "\u0623": "\u0627",  # أ -> ا
    "\u0625": "\u0627",  # إ -> ا
    "\u0622": "\u0627",  # آ -> ا
    "\u0671": "\u0627",  # ٱ -> ا
    "\u0629": "\u0647",  # ة -> ه
    "\u0649": "\u064A",  # ى -> ي
    "\u0624": "\u0648",  # ؤ -> و
    "\u0626": "\u064A",  # ئ -> ي
    "\u0621": "",        # hamza dropped
}


def normalize(input_text: Optional[str]) -> str:
    """Fold a string for cross-script, accent-insensitive comparison."""
    if not input_text:
        return ""
    s = unicodedata.normalize("NFD", input_text)
    s = "".join(ch for ch in s if ord(ch) not in _ARABIC_DIACRITICS)
    s = unicodedata.normalize("NFC", s)
    s = "".join(ARABIC_LETTER_FOLDS.get(ch, ch) for ch in s)
    s = s.casefold()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("\u2019", "").replace("'", "").replace("`", "")
    out = []
    for ch in s:
        if ch.isalnum() or "\u0600" <= ch <= "\u06FF":
            out.append(ch.lower())
        else:
            out.append(" ")
    return " ".join("".join(out).split())


def _squash(s: str) -> str:
    return s.replace(" ", "")


def score_one(query: str, *targets: Optional[str]) -> float:
    q = normalize(query)
    if not q:
        return 0.0
    qs = _squash(q)
    best = 0.0
    for raw in targets:
        if not raw:
            continue
        t = normalize(raw)
        if not t:
            continue
        ts = _squash(t)
        if t == q or ts == qs:
            best = max(best, 1.0)
        elif t.startswith(q) or ts.startswith(qs):
            best = max(best, 0.9)
        elif any(w.startswith(q) for w in t.split(" ")):
            best = max(best, 0.85)
        elif q in t or qs in ts:
            best = max(best, 0.8)
        if best == 1.0:
            break
    return best


T = TypeVar("T")


@dataclass(frozen=True)
class Scored(Generic[T]):
    item: T
    score: float


def search_bucket(items: Iterable[T], names, ar_name, query: str, limit: int,
                  lang: Optional[str] = None) -> List[Scored]:
    scored: List[Scored] = []
    for item in items:
        if lang == "ar" and not ar_name(item):
            continue
        s = score_one(query, *names(item))
        if s > 0:
            scored.append(Scored(item, s))
    scored.sort(key=lambda x: -x.score)
    return scored[:limit]


@dataclass(frozen=True)
class SearchResult:
    wilayas: List[Scored]
    moughataas: List[Scored]
    communes: List[Scored]
    best: Optional[Scored] = None


def search(query: str, limit: int = 10, lang: Optional[str] = None) -> SearchResult:
    """Cross-script fuzzy search (French / ASCII / Arabic) across all levels."""
    wilayas = search_bucket(_WILAYAS, lambda w: [w.name_fr, w.name_en, w.name_ar,
                                                 w.capital, w.capital_ar, *w.aliases],
                            lambda w: w.name_ar, query, limit, lang)
    moughataas = search_bucket(_MOUGHATAAS, lambda m: [m.name_fr, m.name_en, m.name_ar,
                                                       m.capital, *m.aliases],
                               lambda m: m.name_ar, query, limit, lang)
    communes = search_bucket(_COMMUNES, lambda c: [c.name_fr, c.name_en, c.name_ar,
                                                   *c.aliases],
                             lambda c: c.name_ar, query, limit, lang)
    pool: List[Scored] = [*wilayas, *moughataas, *communes]
    pool.sort(key=lambda x: -x.score)
    return SearchResult(wilayas=wilayas, moughataas=moughataas,
                        communes=communes, best=pool[0] if pool else None)
