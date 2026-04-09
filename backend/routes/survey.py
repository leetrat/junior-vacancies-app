"""
Принимает ответы опроса или резюме,
возвращает рекомендованный cluster_id и список всех кластеров
"""

import io
from flask import Blueprint, request, jsonify
import pdfplumber
from docx import Document
from data.model import detect_cluster, detect_cluster_from_answers, extract_skills
from data.cluster_data import CLUSTER_INFO, CLUSTER_TAGS, PRESET_SKILLS


survey_bp = Blueprint("survey", __name__)


def _build_clusters_list() -> list:
    """Возвращает список всех кластеров с тегами для фронта"""
    result = []
    for cid, info in CLUSTER_INFO.items():
        tags = CLUSTER_TAGS.get(cid, ("", "", "", ""))
        desc = str(info.get("description", "") or "")
        result.append({
            "cid":               cid,
            "name":              info.get("name", ""),
            "description":       desc,
            "descriptionShort":  desc[:90] + "…" if len(desc) > 90 else desc,
            "techTagClass":      tags[0],
            "techLabel":         tags[1],
            "overworkTagClass":  tags[2],
            "overworkLabel":     tags[3],
        })
    return result


@survey_bp.route("/api/survey", methods=["POST"])
def survey():
    tech      = request.form.get("it_experience")
    load      = request.form.get("load_level")
    corporate = request.form.get("corporate")

    work_formats = request.form.getlist("work_format")
    salary_from  = request.form.get("salary_from", "")
    salary_to    = request.form.get("salary_to", "")

    resume_file  = request.files.get("resume")
    file_content = None
    skills       = []
    resume_used  = False

    if resume_file and resume_file.filename:
        resume_used = True
        filename    = resume_file.filename
        file_bytes  = resume_file.read()

        if filename.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    file_content = "\n".join(
                        p.extract_text() for p in pdf.pages if p.extract_text()
                    )
            except Exception as e:
                file_content = str(e)

        elif filename.lower().endswith(".docx"):
            try:
                doc = Document(io.BytesIO(file_bytes))
                file_content = "\n".join(
                    p.text for p in doc.paragraphs if p.text.strip()
                )
            except Exception as e:
                file_content = str(e)
        else:
            file_content = file_bytes.decode("utf-8", errors="ignore")

    if file_content:
        cluster_id = detect_cluster(file_content)
        skills     = extract_skills(file_content)
    else:
        cluster_id = detect_cluster_from_answers(tech, load, corporate)

    cluster_id = int(cluster_id)

    return jsonify({
        "clusterId":     cluster_id,
        "clusterName":   CLUSTER_INFO.get(cluster_id, {}).get("name", "—"),
        "clustersList":  _build_clusters_list(),
        "presetSkills":  PRESET_SKILLS,
        "resumeUsed":    resume_used,
        "skills":        skills,
        "workFormats":   work_formats,
        "salaryFrom":    salary_from,
        "salaryTo":      salary_to,
    })
