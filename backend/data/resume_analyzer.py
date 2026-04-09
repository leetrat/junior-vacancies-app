"""
Гибридный анализ резюме: быстрый парсинг + LLM-комментарий
"""

import re
import json
import hashlib
from typing import Optional


_llm = None
_last_hash: Optional[str] = None


def _get_llm():
    global _llm
    if _llm is None:
        try:
            import os
            from llama_cpp import Llama
            model_path = os.path.join(os.path.dirname(__file__), "model.gguf")
            if os.path.exists(model_path) and os.path.getsize(model_path) > 1_000_000_000:
                _llm = Llama(
                    model_path=model_path,
                    n_ctx=4096,
                    n_threads=4,
                    n_gpu_layers=-1,
                    verbose=False,
                )
        except Exception as e:
            print(f"[LLM] Не удалось загрузить модель: {e}")
    return _llm


# Парсинг портфолио
def check_portfolio(resume_text: str) -> dict:
    text = resume_text.lower()
    has_github = any(w in text for w in ["github", "гитхаб", "gitlab", "bitbucket"])
    links = re.findall(r"github\.com/[\w\-]+/[\w\-]+", text)
    project_count = len(links)
    has_enough = project_count >= 3

    if not has_github and not project_count:
        rec = "Добавьте GitHub с 2–3 pet-проектами — это значительно повысит шансы!"
    elif not has_github:
        rec = "Добавьте ссылку на GitHub, где выложены ваши проекты"
    elif not has_enough:
        rec = f"У вас {project_count} проект(ов). Добавьте ещё {3 - project_count} pet-проекта"
    else:
        rec = "Отличное портфолио! Продолжайте пополнять GitHub новыми проектами"

    return {
        "has_github":        has_github,
        "project_count":     project_count,
        "has_enough_projects": has_enough,
        "recommendation":    rec,
    }


# Быстрый парсинг резюме
_SKILL_KEYWORDS = {
    "python":      ["python", "питон"],
    "java":        ["java"],
    "c#":          ["c#", "csharp"],
    "c++":         ["c++"],
    "javascript":  ["javascript", "js"],
    "typescript":  ["typescript", "ts"],
    "go":          ["golang", " go "],
    "kotlin":      ["kotlin"],
    "swift":       ["swift"],
    "php":         ["php"],
    "sql":         ["sql"],
    "postgresql":  ["postgresql", "postgres"],
    "mysql":       ["mysql"],
    "mongodb":     ["mongodb", "mongo"],
    "redis":       ["redis"],
    "docker":      ["docker"],
    "kubernetes":  ["kubernetes", "k8s"],
    "git":         ["git"],
    "react":       ["react"],
    "vue":         ["vue"],
    "angular":     ["angular"],
    "django":      ["django"],
    "flask":       ["flask"],
    "fastapi":     ["fastapi"],
    "spring":      ["spring"],
    "tensorflow":  ["tensorflow", "tf"],
    "pytorch":     ["pytorch"],
    "pandas":      ["pandas"],
    "numpy":       ["numpy"],
    "scikit":      ["scikit", "sklearn"],
    "linux":       ["linux"],
    "aws":         ["aws", "amazon web services"],
    "azure":       ["azure"],
    "html":        ["html"],
    "css":         ["css"],
    "figma":       ["figma"],
    "1c":          ["1с", "1c"],
}

_FIELD_REQUIREMENTS = {
    "python-разработчик":   ["python", "django", "flask", "fastapi", "sql", "git", "docker"],
    "java-разработчик":     ["java", "spring", "sql", "git", "docker", "maven"],
    "frontend-разработчик": ["javascript", "html", "css", "react", "git"],
    "аналитик данных":      ["python", "sql", "pandas", "numpy", "scikit", "git"],
    "devops-инженер":       ["linux", "docker", "kubernetes", "git", "aws"],
    "тестировщик":          ["git", "sql", "python", "postman"],
    "android-разработчик":  ["kotlin", "java", "git", "android"],
    "ios-разработчик":      ["swift", "git", "ios"],
}


def parse_resume_fast(resume_text: str, target_field: str) -> dict:
    text = resume_text.lower()

    # Опыт
    years = 0.0
    for pat in [
        r"опыт работы\s*[—\-]\s*(\d+(?:\.\d+)?)\s*месяц",
        r"опыт работы\s*[—\-]\s*(\d+(?:\.\d+)?)\s*год",
        r"опыт работы:\s*(\d+(?:\.\d+)?)\s*месяц",
        r"опыт работы:\s*(\d+(?:\.\d+)?)\s*год",
    ]:
        m = re.search(pat, text)
        if m:
            val = float(m.group(1))
            years = val / 12 if "месяц" in pat else val
            break
    if years == 0 and ("стажёр" in text or "стажер" in text):
        years = 0.5

    has_education = any(w in text for w in
                        ["образование", "вуз", "университет", "бакалавр", "магистр", "диплом", "курсы"])

    # Навыки
    all_skills = []
    for skill, keywords in _SKILL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            all_skills.append(skill)

    # Релевантные навыки по специализации
    field_key = target_field.lower().strip()
    required  = _FIELD_REQUIREMENTS.get(field_key, [])
    relevant  = [s for s in all_skills if s in required]
    gaps      = [r for r in required if r not in all_skills]

    # Портфолио
    portfolio = check_portfolio(resume_text)
    project_count = portfolio["project_count"]

    # Предварительная оценка
    score = 0
    score += min(years * 15, 30)
    score += min(len(relevant) * 8, 40)
    score += min(project_count * 5, 15)
    if has_education: score += 10
    score += 5  # базовый балл
    score = min(int(score), 100)

    if score >= 75:   level = "Senior"
    elif score >= 55: level = "Middle"
    elif score >= 35: level = "Junior"
    else:             level = "Trainee"

    return {
        "years":          round(years, 1),
        "has_experience": years > 0,
        "has_education":  has_education,
        "all_skills":     all_skills,
        "relevant_skills": relevant,
        "gaps":           gaps,
        "project_count":  project_count,
        "pre_score":      score,
        "pre_level":      level,
    }


# Гибридный анализ (парсинг + LLM)
def analyze_resume_hybrid(resume_text: str, career_field: str) -> dict:
    global _last_hash
    parsed = parse_resume_fast(resume_text, career_field)

    hr_comment      = ""
    fun_motivation  = ""

    llm = _get_llm()
    if llm:
        curr_hash = hashlib.md5(f"{career_field}{resume_text[:100]}".encode()).hexdigest()
        if curr_hash != _last_hash:
            try: llm.reset()
            except Exception: pass
            _last_hash = curr_hash

        prompt = f"""Ты дружелюбный HR-консультант в IT.
Кандидат хочет стать {career_field}.
Данные из резюме:
- Опыт: {parsed['years']} лет
- Образование: {'есть' if parsed['has_education'] else 'нет'}
- Навыки: {', '.join(parsed['all_skills']) or 'не указаны'}
- Пет-проектов: {parsed['project_count']}
- Релевантные навыки: {', '.join(parsed['relevant_skills']) or 'нет'}
- Чего не хватает: {', '.join(parsed['gaps']) or 'всё есть'}
- Оценка: {parsed['pre_score']}/100, уровень: {parsed['pre_level']}
Напиши ТОЛЬКО JSON:
{{
  "hr_comment": "твой дружелюбный комментарий (2-3 предложения на русском)",
  "fun_motivation": "короткая мотивирующая шутка или метафора про {career_field}"
}}"""
        try:
            raw = llm(prompt, max_tokens=300, temperature=0.5)["choices"][0]["text"].strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            s, e = raw.find("{"), raw.rfind("}")
            if s != -1 and e != -1:
                obj = json.loads(raw[s:e+1])
                hr_comment     = obj.get("hr_comment", "")
                fun_motivation = obj.get("fun_motivation", "")
        except Exception as ex:
            print(f"[LLM] Ошибка генерации: {ex}")

    return {
        "target_field":     career_field,
        "level":            parsed["pre_level"],
        "level_score":      parsed["pre_score"],
        "experience_years": parsed["years"],
        "has_experience":   parsed["has_experience"],
        "has_education":    parsed["has_education"],
        "extracted_skills": parsed["all_skills"],
        "strengths":        parsed["relevant_skills"],
        "gaps":             parsed["gaps"],
        "project_count":    parsed["project_count"],
        "recommendations":  [f"Изучите {g}" for g in parsed["gaps"][:4]],
        "hr_comment":       hr_comment,
        "fun_motivation":   fun_motivation,
        "llm_available":    bool(llm),
    }
