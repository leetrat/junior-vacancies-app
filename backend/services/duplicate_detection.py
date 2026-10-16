"""
Поиск потенциальных дубликатов вакансий.

Вакансии сравниваются по названию, компании и описанию. Перед сравнением
текст нормализуется (снимается HTML-разметка, регистр, пунктуация и лишние
пробелы), поэтому записи, отличающиеся только форматированием, распознаются
как дубликаты.

Правила классификации:
  * если у вакансии отсутствует название или компания, пара не сравнивается;
  * названия компаний должны совпадать после нормализации — одинаковые
    должности в разных компаниях не считаются дубликатами;
  * итоговая оценка score — взвешенная комбинация схожести названия и
    описания (при отсутствии описания вес перенормируется на название);
  * пара считается дубликатом, если score >= threshold;
  * если нормализованные название, компания и описание совпадают,
    matchType="exact", иначе matchType="similar".

Обнаружение дубликатов не изменяет исходные записи: на выход возвращаются
только идентификаторы, оценки схожести и группировки.
"""

from __future__ import annotations

import html
import math
import os
import re
from difflib import SequenceMatcher
from numbers import Real
from typing import Any, Dict, List, Optional

DEFAULT_SIMILARITY_THRESHOLD = 0.85

TITLE_WEIGHT = 0.6
DESCRIPTION_WEIGHT = 0.4

TITLE_KEYS = ("title", "name")
COMPANY_KEYS = ("company", "employer_name", "employer")
DESCRIPTION_KEYS = ("description", "minimal_clean_text", "clean_text", "descr")
ID_KEYS = ("id", "vacancy_id")

_COMPANY_NOISE = {
    "ооо", "зао", "пао", "ао", "нао", "оао",
    "llc", "ltd", "inc", "corp", "gmbh", "plc",
}

_TAG_RE = re.compile(r"<[^>]+>")
_NON_WORD_RE = re.compile(r"[\W_]+", re.UNICODE)
_WS_RE = re.compile(r"\s+")

_EPSILON = 1e-9


def get_default_threshold() -> float:
    """Порог из переменной окружения DUPLICATE_SIMILARITY_THRESHOLD либо значение по умолчанию."""
    raw = os.getenv("DUPLICATE_SIMILARITY_THRESHOLD")
    if raw is None or not str(raw).strip():
        return DEFAULT_SIMILARITY_THRESHOLD
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_SIMILARITY_THRESHOLD
    if not math.isfinite(value) or not (0.0 < value <= 1.0):
        return DEFAULT_SIMILARITY_THRESHOLD
    return value


def _validate_threshold(threshold: Any) -> float:
    if isinstance(threshold, bool) or not isinstance(threshold, Real):
        raise ValueError("Порог схожести должен быть числом от 0 до 1.")
    value = float(threshold)
    if not math.isfinite(value) or not (0.0 < value <= 1.0):
        raise ValueError("Порог схожести должен быть в диапазоне (0; 1].")
    return value


def normalize_text(value: Any) -> str:
    """Нормализует текст: HTML, регистр, пунктуация и пробелы."""
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = _TAG_RE.sub(" ", text)
    text = text.lower()
    text = _NON_WORD_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def normalize_company(value: Any) -> str:
    """Нормализует название компании, отбрасывая юридические формы."""
    tokens = [t for t in normalize_text(value).split() if t not in _COMPANY_NOISE]
    return " ".join(tokens)


def text_similarity(left: Any, right: Any) -> float:
    """Коэффициент схожести двух текстов 0..1 после нормализации."""
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def _get_field(vacancy: Dict[str, Any], keys: tuple) -> Any:
    for key in keys:
        value = vacancy.get(key)
        if value is None:
            continue
        if isinstance(value, dict):
            value = value.get("name")
        if value is not None and str(value).strip() != "":
            return value
    return None


def _get_id(vacancy: Dict[str, Any], fallback: Any) -> str:
    for key in ID_KEYS:
        value = vacancy.get(key)
        if value is not None and str(value).strip() != "":
            return str(value)
    return str(fallback)


def compare_vacancies(left: Dict[str, Any], right: Dict[str, Any], threshold: float) -> Optional[Dict[str, Any]]:
    """Сравнивает две вакансии и возвращает результат, если они дубликаты, иначе None."""
    title_l = normalize_text(_get_field(left, TITLE_KEYS))
    title_r = normalize_text(_get_field(right, TITLE_KEYS))
    if not title_l or not title_r:
        return None

    company_l = normalize_company(_get_field(left, COMPANY_KEYS))
    company_r = normalize_company(_get_field(right, COMPANY_KEYS))
    if not company_l or not company_r or company_l != company_r:
        return None

    title_sim = SequenceMatcher(None, title_l, title_r).ratio()

    desc_l = normalize_text(_get_field(left, DESCRIPTION_KEYS))
    desc_r = normalize_text(_get_field(right, DESCRIPTION_KEYS))
    if desc_l and desc_r:
        desc_sim: Optional[float] = SequenceMatcher(None, desc_l, desc_r).ratio()
        score = TITLE_WEIGHT * title_sim + DESCRIPTION_WEIGHT * desc_sim
    else:
        desc_sim = None
        score = title_sim

    if score + _EPSILON < threshold:
        return None

    exact = (
        title_l == title_r
        and company_l == company_r
        and (desc_l == desc_r or (not desc_l and not desc_r))
    )

    return {
        "score": round(score, 4),
        "titleSimilarity": round(title_sim, 4),
        "descriptionSimilarity": round(desc_sim, 4) if desc_sim is not None else None,
        "matchType": "exact" if exact else "similar",
    }


def find_duplicate_pairs(vacancies: List[Dict[str, Any]], threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    """Возвращает список пар-дубликатов с оценкой схожести."""
    if threshold is None:
        threshold = get_default_threshold()
    else:
        threshold = _validate_threshold(threshold)

    pairs: List[Dict[str, Any]] = []
    for i in range(len(vacancies)):
        for j in range(i + 1, len(vacancies)):
            result = compare_vacancies(vacancies[i], vacancies[j], threshold)
            if result is None:
                continue
            result = {
                "idA": _get_id(vacancies[i], i),
                "idB": _get_id(vacancies[j], j),
                **result,
            }
            pairs.append(result)

    pairs.sort(key=lambda p: p["score"], reverse=True)
    return pairs


def find_duplicate_groups(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Объединяет пары в группы через union-find и возвращает группы размера >= 2."""
    parent: Dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: str, b: str) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    scores: Dict[str, float] = {}
    for pair in pairs:
        union(pair["idA"], pair["idB"])
        for node in (pair["idA"], pair["idB"]):
            scores[node] = max(scores.get(node, 0.0), pair["score"])

    members: Dict[str, List[str]] = {}
    for node in parent:
        members.setdefault(find(node), []).append(node)

    groups = []
    for root, nodes in members.items():
        if len(nodes) < 2:
            continue
        group_score = max(scores.get(n, 0.0) for n in nodes)
        groups.append({
            "ids": sorted(nodes),
            "size": len(nodes),
            "score": round(group_score, 4),
        })

    groups.sort(key=lambda g: (-g["size"], -g["score"]))
    return groups


def detect_duplicates(vacancies: List[Dict[str, Any]], threshold: Optional[float] = None) -> Dict[str, Any]:
    """Ищет дубликаты среди вакансий, не изменяя исходные записи."""
    if not isinstance(vacancies, list):
        raise ValueError("vacancies должен быть списком.")

    if threshold is None:
        resolved = get_default_threshold()
    else:
        resolved = _validate_threshold(threshold)

    pairs = find_duplicate_pairs(vacancies, resolved)
    groups = find_duplicate_groups(pairs)

    return {
        "threshold": resolved,
        "vacancyCount": len(vacancies),
        "pairCount": len(pairs),
        "groupCount": len(groups),
        "pairs": pairs,
        "groups": groups,
    }
