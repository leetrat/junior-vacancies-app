"""
backend/services/duplicate_detection.py
Поиск потенциальных дубликатов вакансий.

Вакансии сравниваются по трём полям (поддерживаются алиасы из датасета
и из API-запросов):
    title        — название вакансии (name / title)
    company      — компания (employer_name / company)
    description  — описание (description / minimal_clean_text)

Перед сравнением текст нормализуется: снимается HTML-разметка, регистр,
пунктуация и лишние пробелы — поэтому вакансии, отличающиеся только
форматированием, распознаются как дубликаты.

Правила классификации:
  * пары, в которых у какой-либо из вакансий отсутствует название или
    компания, не сравниваются (недостаточно данных);
  * компании должны совпадать после нормализации (регистр, пунктуация и
    юридические формы вроде ООО/LLC игнорируются) — одинаковые названия
    в разных компаниях не считаются дублями;
  * названия должны совпадать схожестью не ниже порога — похожие описания
    при разных должностях не приводят к ложным дублям;
  * итоговая оценка score — взвешенная комбинация схожести названия и
    описания; пара считается дубликатом, если score >= threshold;
  * если описание отсутствует у одной или обеих вакансий, оно исключается
    из расчёта, а веса перенормализуются (оценка определяется названием);
  * полностью совпавшие нормализованные поля дают matchType="exact",
    остальные случаи — matchType="similar".

Обнаружение дубликатов ничего не изменяет в исходных записях:
на выход возвращаются только идентификаторы и оценки схожести.
"""

from __future__ import annotations

import html
import math
import os
import re
from difflib import SequenceMatcher
from functools import lru_cache
from numbers import Real
from typing import Any, Iterable, Optional

# Порог по умолчанию; переопределяется переменной окружения
# DUPLICATE_SIMILARITY_THRESHOLD или аргументом `threshold` в запросе.
DEFAULT_SIMILARITY_THRESHOLD = 0.85

# Компании сравниваются точно (после нормализации), поэтому в оценку
# схожести входят только название и описание.
TITLE_WEIGHT = 0.6
DESCRIPTION_WEIGHT = 0.4

TITLE_KEYS = ("title", "name")
COMPANY_KEYS = ("company", "employer_name", "employer")
DESCRIPTION_KEYS = ("description", "descr", "minimal_clean_text", "clean_text")

# Юридические формы, не влияющие на имя компании
_COMPANY_NOISE = {
    "ооо", "зао", "пао", "ао", "нао", "оао",
    "llc", "ltd", "inc", "corp", "gmbh", "plc",
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[\W_]+", re.UNICODE)


def get_default_threshold() -> float:
    """Порог из переменной окружения DUPLICATE_SIMILARITY_THRESHOLD (или по умолчанию)."""
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
        raise ValueError("Порог должен быть числом от 0 до 1.")
    value = float(threshold)
    if not math.isfinite(value) or not (0.0 < value <= 1.0):
        raise ValueError("Порог должен быть в диапазоне (0; 1].")
    return value


def normalize_text(value: Any) -> str:
    """Нормализация текста: без HTML, регистра, пунктуации и лишних пробелов."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value != value:  # NaN / np.nan
        return ""
    if isinstance(value, (list, tuple, set, frozenset)):
        return normalize_text(" ".join(str(v) for v in value))
    if not isinstance(value, str):
        value = str(value)
    text = html.unescape(value)
    text = _TAG_RE.sub(" ", text)
    text = text.lower()
    text = _NON_WORD_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def _normalize_company(value: Any) -> str:
    """Нормализация названия компании с учётом юридических форм (ООО, LLC...)."""
    tokens = [t for t in normalize_text(value).split() if t not in _COMPANY_NOISE]
    return " ".join(tokens)


def _sim(normalized_a: str, normalized_b: str) -> float:
    """Схожесть двух уже нормализованных строк (0..1).

    Сравнение выполняется в каноническом порядке аргументов и кэшируется:
    при обработке больших наборов вакансий одни и те же тексты встречаются
    многократно, а сравнение строк — самая дорогая операция.
    """
    if normalized_a == normalized_b:
        return 1.0
    if not normalized_a or not normalized_b:
        return 0.0
    if normalized_b < normalized_a:
        normalized_a, normalized_b = normalized_b, normalized_a
    return _sim_cached(normalized_a, normalized_b)


@lru_cache(maxsize=200_000)
def _sim_cached(normalized_a: str, normalized_b: str) -> float:
    return SequenceMatcher(None, normalized_a, normalized_b, autojunk=False).ratio()


def text_similarity(raw_a: Any, raw_b: Any) -> float:
    """Схожесть двух произвольных значений после нормализации (0..1)."""
    return _sim(normalize_text(raw_a), normalize_text(raw_b))


def _pick(vacancy: dict, keys: Iterable[str]) -> Any:
    for key in keys:
        if key in vacancy and vacancy[key] is not None:
            value = vacancy[key]
            if isinstance(value, dict):  # например, employer: {"name": ...}
                value = value.get("name")
            return value
    return None


def _vacancy_id(vacancy: dict, index: int) -> str:
    raw = vacancy.get("id")
    if raw is None:
        return f"#{index}"
    if isinstance(raw, float) and raw != raw:  # NaN
        return f"#{index}"
    text = str(raw).strip()
    return text if text else f"#{index}"


def _compare_normalized(
    title_a: str, company_a: str, description_a: str,
    title_b: str, company_b: str, description_b: str,
    threshold: float,
) -> Optional[dict]:
    """Сравнение уже нормализованных полей. None — если данных недостаточно
    или пара не проходит пороги."""
    if not title_a or not title_b or not company_a or not company_b:
        return None  # недостаточно данных для сравнения

    # Компании обязаны совпадать: одинаковое название в разных
    # компаниях не делает вакансии дубликатами.
    if company_a != company_b:
        return None

    # Название также должно совпадать схожестью не ниже порога,
    # чтобы похожие описания разных должностей не считались дублями.
    title_sim = _sim(title_a, title_b)
    if title_sim < threshold:
        return None

    if description_a and description_b:
        description_sim = _sim(description_a, description_b)
        score = (
            TITLE_WEIGHT * title_sim
            + DESCRIPTION_WEIGHT * description_sim
        )
    else:
        # Описание отсутствует у одной или обеих вакансий — решение
        # принимается по названию.
        score = title_sim

    score = round(min(max(score, 0.0), 1.0), 4)
    if score < threshold:
        return None

    exact = (
        title_a == title_b
        and company_a == company_b
        and description_a == description_b
    )
    return {"score": score, "matchType": "exact" if exact else "similar"}


def compare_vacancies(
    vacancy_a: dict,
    vacancy_b: dict,
    threshold: Optional[float] = None,
) -> Optional[dict]:
    """Сравнить две вакансии.

    Возвращает {"score": float, "matchType": "exact"|"similar"}, если вакансии
    являются дубликатами при заданном пороге, иначе None.
    """
    threshold = get_default_threshold() if threshold is None else _validate_threshold(threshold)
    if not isinstance(vacancy_a, dict) or not isinstance(vacancy_b, dict):
        return None
    return _compare_normalized(
        normalize_text(_pick(vacancy_a, TITLE_KEYS)),
        _normalize_company(_pick(vacancy_a, COMPANY_KEYS)),
        normalize_text(_pick(vacancy_a, DESCRIPTION_KEYS)),
        normalize_text(_pick(vacancy_b, TITLE_KEYS)),
        _normalize_company(_pick(vacancy_b, COMPANY_KEYS)),
        normalize_text(_pick(vacancy_b, DESCRIPTION_KEYS)),
        threshold,
    )


def find_duplicate_pairs(
    vacancies: Iterable[Any],
    threshold: Optional[float] = None,
) -> list[dict]:
    """Найти все пары дубликатов.

    Возвращает список {"idA", "idB", "score", "matchType"},
    отсортированный по убыванию score. Исходные записи не изменяются.
    """
    threshold = get_default_threshold() if threshold is None else _validate_threshold(threshold)
    items = []
    for index, vacancy in enumerate(vacancies):
        if not isinstance(vacancy, dict):
            continue
        title = normalize_text(_pick(vacancy, TITLE_KEYS))
        company = _normalize_company(_pick(vacancy, COMPANY_KEYS))
        if not title or not company:
            continue  # недостаточно данных — не сравниваем
        items.append({
            "index": index,
            "id": _vacancy_id(vacancy, index),
            "title": title,
            "company": company,
            "description": normalize_text(_pick(vacancy, DESCRIPTION_KEYS)),
        })

    # Группировка по нормализованной компании: вакансии разных компаний
    # не могут быть дубликатами, поэтому не сравниваются вовсе.
    buckets: dict[str, list[dict]] = {}
    for item in items:
        buckets.setdefault(item["company"], []).append(item)

    pairs = []
    for company in sorted(buckets):
        group = buckets[company]
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                item_a, item_b = group[i], group[j]
                result = _compare_normalized(
                    item_a["title"], item_a["company"], item_a["description"],
                    item_b["title"], item_b["company"], item_b["description"],
                    threshold,
                )
                if result is None:
                    continue
                pairs.append({
                    "idA": item_a["id"],
                    "idB": item_b["id"],
                    "score": result["score"],
                    "matchType": result["matchType"],
                })

    pairs.sort(key=lambda pair: (-pair["score"], pair["idA"], pair["idB"]))
    return pairs


def _group_pairs(pairs: list[dict]) -> list[dict]:
    """Объединить пары в группы дубликатов (union-find)."""
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(node_a: str, node_b: str) -> None:
        root_a, root_b = find(node_a), find(node_b)
        if root_a != root_b:
            parent[root_b] = root_a

    # Максимальная оценка хранится по каждому id, затем агрегируется
    # по итоговой группе — корни могут меняться по ходу объединений.
    score_by_id: dict[str, float] = {}
    for pair in pairs:
        union(pair["idA"], pair["idB"])
        for vacancy_id in (pair["idA"], pair["idB"]):
            score_by_id[vacancy_id] = max(
                score_by_id.get(vacancy_id, 0.0), pair["score"]
            )

    grouped: dict[str, list[str]] = {}
    for vacancy_id in parent:
        grouped.setdefault(find(vacancy_id), []).append(vacancy_id)

    groups = []
    for _root, ids in grouped.items():
        unique_ids = sorted(set(ids))
        if len(unique_ids) < 2:
            continue
        groups.append({
            "ids": unique_ids,
            "size": len(unique_ids),
            "score": round(max(score_by_id.get(v, 0.0) for v in unique_ids), 4),
        })
    groups.sort(key=lambda group: (-group["size"], -group["score"], group["ids"]))
    return groups


def find_duplicate_groups(
    vacancies: Iterable[Any],
    threshold: Optional[float] = None,
) -> list[dict]:
    """Найти группы дубликатов: {"ids": [...], "size": n, "score": max}."""
    return _group_pairs(find_duplicate_pairs(vacancies, threshold))


def detect_duplicates(
    vacancies: Optional[Iterable[Any]],
    threshold: Optional[float] = None,
) -> dict:
    """Полный прогон: пары + группы дубликатов.

    Возвращает dict с threshold, vacancyCount, pairCount, groupCount,
    pairs и groups. Исходные записи не изменяются.
    """
    threshold = get_default_threshold() if threshold is None else _validate_threshold(threshold)
    records = list(vacancies) if vacancies is not None else []
    pairs = find_duplicate_pairs(records, threshold)
    groups = _group_pairs(pairs)
    return {
        "threshold": threshold,
        "vacancyCount": len(records),
        "pairCount": len(pairs),
        "groupCount": len(groups),
        "pairs": pairs,
        "groups": groups,
    }
