"""
Анализ вакансии с hh.ru по ссылке
"""

import re
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from flask import Blueprint, request, jsonify
from bs4 import BeautifulSoup
from data.cluster_data import EXP_MAP, SCHEDULE_MAP
import os
import requests

# Полностью убираем все прокси из окружения
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(var, None)

def fetch_hh(vacancy_id):
    url = f"https://api.hh.ru/vacancies/{vacancy_id}"
    # proxies=None заставляет requests игнорировать системные прокси
    try:
        response = requests.get(url, timeout=10, proxies={"http": None, "https": None})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к HH: {e}")
        return None

vacancy = fetch_hh(131615180)
print(vacancy)


vacancy_analysis_bp = Blueprint("vacancy_analysis", __name__)


def _extract_id(url: str) -> str:
    m = re.search(r"/vacancy/(\d+)", url)
    if not m:
        raise ValueError("Невалидная ссылка: не найден ID вакансии.")
    return m.group(1)


def _get_vacancy_data(url: str) -> dict:
    vid = _extract_id(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }

    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    response = session.get(
        f"https://api.hh.ru/vacancies/{vid}",
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"hh.ru API вернул {response.status_code}: {response.text}")

    return response.json()


def _clean_text(raw: str) -> str:
    if not raw:
        return ""
    return BeautifulSoup(raw, "html.parser").get_text(" ").lower()


# словари редфлагов
_EXPERIENCE_MISMATCH = [
    'требуется опыт', 'требуется опыт работы', 'необходим опыт',
    'нужен опыт', 'важен опыт', 'опыт обязателен', 'опыт работы обязателен',
]
_LOW_SALARY_THRESHOLD = 30_000
_TOXIC_CULTURE = [
    "стрессоустойчивость", "работа в режиме многозадачности",
    "готовность к переработкам", "ненормированный рабочий день",
    "работа на результат любой ценой",
]
_NO_MENTORSHIP = ["самостоятельно разберётесь", "без наставника", "сразу к работе"]
_LETTER_AND_TEST = ["сопроводительное письмо", "тестовое задание"]


def _analyze_red_flags(vacancy_data: dict) -> tuple[str, int]:
    if not vacancy_data:
        return "Ошибка: нет данных вакансии", 0

    snippet = vacancy_data.get("snippet")
    if not isinstance(snippet, dict):
        snippet = {}

    parts = [
        vacancy_data.get("name", ""),
        (vacancy_data.get("snippet") or {}).get("responsibility", ""),
        (vacancy_data.get("snippet") or {}).get("requirement", ""),
        vacancy_data.get("description", ""),
    ]
    text = _clean_text(" ".join(p for p in parts if p))

    flags = []
    exp_id = (vacancy_data.get("experience") or {}).get("id", "")

    if exp_id == "noExperience":
        if any(m in text for m in _EXPERIENCE_MISMATCH):
            flags.append("⚠️ Требуют опыт, хотя указано «без опыта»")

    salary = vacancy_data.get("salary") or {}
    min_s  = salary.get("from")
    if min_s and min_s < _LOW_SALARY_THRESHOLD:
        flags.append(f"⚠️ Низкая зарплата: от {int(min_s)} ₽")

    if any(m in text for m in _TOXIC_CULTURE):
        flags.append("⚠️ Требуется креативность / софтскиллы / заряженность, может говорить о токсичной культуре")

    if any(m in text for m in _NO_MENTORSHIP):
        flags.append("⚠️ Нет упоминаний менторства/обучения для позиции без опыта")

    letter_test = sum(1 for m in _LETTER_AND_TEST if m in text)
    if letter_test == 2:
        flags.append("⚠️ Двойной барьер: сопроводительное письмо и входной тест")

    if not salary:
        flags.append("⚠️ Зарплата не указана")

    return "; ".join(flags), len(flags)


@vacancy_analysis_bp.route("/api/analyze_vacancy", methods=["POST"])
def analyze_vacancy():
    body        = request.get_json(force=True)
    vacancy_url = (body or {}).get("vacancyUrl", "").strip()

    if not vacancy_url:
        return jsonify({"error": "Не передана ссылка"}), 400

    try:
        data = _get_vacancy_data(vacancy_url)
        if not isinstance(data, dict):
                raise Exception("Некорректный ответ от hh.ru")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Ошибка запроса к hh.ru: {e}"}), 502

    try:
        red_flags_text, red_flags_count = _analyze_red_flags(data)
    except Exception as e:
        return jsonify({"error": f"Ошибка анализа: {e}"}), 500

    salary_data = data.get("salary") or {}
    min_s = salary_data.get("from")
    max_s = salary_data.get("to")
    if min_s and max_s: salary = f"{int(min_s)} – {int(max_s)} ₽"
    elif min_s:         salary = f"от {int(min_s)} ₽"
    elif max_s:         salary = f"до {int(max_s)} ₽"
    else:               salary = "не указана"

    raw_skills = data.get("key_skills", [])
    skills_list = [
        (s.get("name") if isinstance(s, dict) else s)
        for s in raw_skills if s
    ]

    vacancy_info = {
        "name":          data.get("name", ""),
        "alternate_url": data.get("alternate_url", "#"),
        "employer_name": (data.get("employer") or {}).get("name", ""),
        "salary":        salary,
        "experience":    EXP_MAP.get((data.get("experience") or {}).get("id"), "—"),
        "work_format":   SCHEDULE_MAP.get((data.get("schedule") or {}).get("id"), "—"),
        "skills_list":   skills_list,
    }

    return jsonify({
        "vacancy":        vacancy_info,
        "redFlagsText":   red_flags_text,
        "redFlagsCount":  red_flags_count,
    })
