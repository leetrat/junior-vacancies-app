"""
backend/routes/duplicates.py
POST /api/duplicates — поиск потенциальных дубликатов вакансий.

Тело запроса (JSON, опционально):
    vacancies  — список вакансий; если не передан, используется весь
                 датасет из data.model
    threshold  — порог схожести (0; 1], по умолчанию
                 DUPLICATE_SIMILARITY_THRESHOLD или 0.85

Ответ: threshold, vacancyCount, pairCount, groupCount, pairs, groups.
Обнаружение дубликатов не изменяет исходные записи вакансий.
"""

from flask import Blueprint, request, jsonify

from services.duplicate_detection import detect_duplicates

duplicates_bp = Blueprint("duplicates", __name__)


@duplicates_bp.route("/api/duplicates", methods=["POST"])
def duplicates():
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    vacancies = body.get("vacancies")
    if vacancies is None:
        # Ленивый импорт: data.model загружает датасет и SBERT-модель.
        from data.model import df_for_clasters
        vacancies = df_for_clasters.to_dict(orient="records")
    elif not isinstance(vacancies, list):
        return jsonify({"error": "Поле vacancies должно быть списком"}), 400

    try:
        result = detect_duplicates(vacancies, threshold=body.get("threshold"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)
