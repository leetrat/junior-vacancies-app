"""
backend/routes/result.py
POST /api/result — вакансии из выбранных кластеров + фильтры + графики.
"""

import ast
import pandas as pd
from flask import Blueprint, request, jsonify

from data.model        import get_cluster_vacancies, top_companies_list, normalize_skill, vacancy_has_skill, top10
from data.cluster_data import CLUSTER_INFO, PRESET_SKILLS, EXP_MAP, SCHEDULE_MAP
from data.analytics    import ClusterAnalyticsService

result_bp = Blueprint("result", __name__)
_analytics = ClusterAnalyticsService()


def _format_vacancy(row, top10_set: set) -> dict:
    flags = int(row.get("red_flag_count", 0))
    if flags == 0:       flag_color = "green"
    elif flags <= 2:     flag_color = "yellow"
    elif flags <= 4:     flag_color = "orange"
    else:                flag_color = "red"

    min_s = row.get("min_salary")
    max_s = row.get("max_salary")
    if pd.notna(min_s) and pd.notna(max_s): salary = f"{int(min_s)} – {int(max_s)} ₽"
    elif pd.notna(min_s):                    salary = f"от {int(min_s)} ₽"
    elif pd.notna(max_s):                    salary = f"до {int(max_s)} ₽"
    else:                                    salary = "не указана"

    try:
        raw = row.get("key_skills", "")
        skills_list = ast.literal_eval(raw) if isinstance(raw, str) else (raw or [])
    except Exception:
        skills_list = []

    name_low   = str(row.get("employer_name", "")).lower().strip()
    accredited = bool(row.get("accredited_it_employer", False))
    if name_low in top10_set and accredited:  company_type = "top"
    elif accredited:                           company_type = "accredited"
    else:                                      company_type = "regular"

    cid = int(row.get("_cluster_id", -1))
    return {
        "id":          str(row.get("id", "")),
        "title":       str(row.get("name", "")),
        "company":     str(row.get("employer_name", "")),
        "salary":      salary,
        "minSalary":   int(min_s) if pd.notna(min_s) else None,
        "maxSalary":   int(max_s) if pd.notna(max_s) else None,
        "format":      SCHEDULE_MAP.get(row.get("schedule_id"), "—"),
        "experience":  EXP_MAP.get(row.get("experience_id"), "—"),
        "skills":      skills_list,
        "flags":       flags,
        "flagColor":   flag_color,
        "flagText":    str(row.get("red_flag", "")) or "",
        "link":        str(row.get("alternate_url", "#")),
        "companyType": company_type,
        "clusterId":   cid,
        "clusterName": CLUSTER_INFO.get(cid, {}).get("name", ""),
    }


@result_bp.route("/api/result", methods=["POST"])
def result():
    body = request.get_json()

    selected_clusters = [int(c) for c in body.get("selectedClusters", [])]
    skill_filters     = body.get("skillFilters", [])
    work_formats      = body.get("workFormats", [])
    salary_from       = body.get("salaryFrom")
    salary_to         = body.get("salaryTo")
    cluster_id_rec    = body.get("clusterIdRecommended")

    if not selected_clusters:
        selected_clusters = [int(cluster_id_rec)] if cluster_id_rec is not None else [0]

    skills_lower = [normalize_skill(s) for s in skill_filters if s.strip()]
    top10_set    = set(top10)

    # ── Собираем вакансии ──────────────────────────────────────────────────
    frames = []
    for cid in selected_clusters:
        chunk = get_cluster_vacancies(cid).copy()
        chunk["_cluster_id"] = cid
        frames.append(chunk)
    all_vacancies = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # ── Фильтры ───────────────────────────────────────────────────────────
    if work_formats and not all_vacancies.empty:
        all_vacancies = all_vacancies[all_vacancies["schedule_id"].isin(work_formats)]

    if salary_from and not all_vacancies.empty:
        try:
            all_vacancies = all_vacancies[all_vacancies["max_salary"].fillna(0) >= int(salary_from)]
        except (ValueError, TypeError):
            pass

    if salary_to and not all_vacancies.empty:
        try:
            all_vacancies = all_vacancies[all_vacancies["min_salary"].fillna(float("inf")) <= int(salary_to)]
        except (ValueError, TypeError):
            pass

    if skills_lower and not all_vacancies.empty:
        mask = all_vacancies.apply(lambda row: vacancy_has_skill(row, skills_lower), axis=1)
        all_vacancies = all_vacancies[mask]

    # ── Сортировка ─────────────────────────────────────────────────────────
    if not all_vacancies.empty:
        all_vacancies["company_top"] = (
            all_vacancies["employer_name"].str.lower().str.strip().isin(top10_set)
        )
        all_vacancies = all_vacancies.sort_values(
            ["company_top", "red_flag_count"], ascending=[False, True]
        )

    # ── Графики ──────────────────────────────────────────────────────────────
    plots = {}
    plots_error = None
    if not all_vacancies.empty:
        plot_df = all_vacancies.copy()
        try:
            plots = _analytics.generate_all(plot_df, needed_graphs=[
                "flags_distribution",
                "top_skills",
                "experience_distribution",
                "top_red_flags",
            ])
        except Exception as e:
            import traceback
            plots_error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            print(f"[analytics] FAILED:\n{plots_error}")

    # ── Статистика зарплаты ────────────────────────────────────────────────
    min_salary = avg_salary = None
    if not all_vacancies.empty and "min_salary" in all_vacancies.columns:
        ms = all_vacancies["min_salary"].min()
        av = all_vacancies["min_salary"].dropna().mean()
        min_salary = int(ms) if pd.notna(ms) else None
        avg_salary = int(av) if pd.notna(av) else None

    vacancies = [_format_vacancy(row, top10_set) for _, row in all_vacancies.iterrows()]
    selected_names = [
        CLUSTER_INFO.get(cid, {}).get("name", f"Кластер {cid}")
        for cid in selected_clusters
    ]

    return jsonify({
        "vacancies":            vacancies,
        "total":                len(vacancies),
        "minSalary":            min_salary,
        "avgSalary":            avg_salary,
        "selectedClusterNames": selected_names,
        "skillFilters":         skill_filters,
        "presetSkills":         PRESET_SKILLS,   # ← всегда возвращаем
        "plots":                plots,
        "plotsError":           plots_error,
    })
