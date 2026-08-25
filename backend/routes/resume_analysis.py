"""
LLM-анализ резюме
"""

import io
from flask import Blueprint, request, jsonify
import pdfplumber
from docx import Document

from data.resume_analyzer import analyze_resume_hybrid

resume_analysis_bp = Blueprint("resume_analysis", __name__)

CAREER_FIELDS = [
    "Python-разработчик", "Backend-разработчик", "Frontend-разработчик",
    "Аналитик данных", "DevOps-инженер", "Тестировщик",
    "ML-инженер", "GameDev",
]


@resume_analysis_bp.route("/api/career_fields", methods=["GET"])
def career_fields():
    return jsonify(CAREER_FIELDS)


@resume_analysis_bp.route("/api/analyze_resume", methods=["POST"])
def analyze_resume():
    career_field = request.form.get("career_field", "").strip()
    resume_file  = request.files.get("resume")

    if not career_field:
        return jsonify({"error": "Не выбрана специализация"}), 400
    if not resume_file or not resume_file.filename:
        return jsonify({"error": "Не загружено резюме"}), 400

    filename   = resume_file.filename
    file_bytes = resume_file.read()
    text       = ""

    if filename.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
        except Exception as e:
            return jsonify({"error": f"Ошибка чтения PDF: {e}"}), 400
    elif filename.lower().endswith(".docx"):
        try:
            doc  = Document(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            return jsonify({"error": f"Ошибка чтения DOCX: {e}"}), 400
    else:
        text = file_bytes.decode("utf-8", errors="ignore")

    if not text.strip():
        return jsonify({"error": "Не удалось извлечь текст из файла"}), 400

    try:
        result = analyze_resume_hybrid(text, career_field)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Ошибка анализа: {e}"}), 500
