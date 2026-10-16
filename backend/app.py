"""
Точка входа Flask-приложения
Запуск: python app.py
"""

from flask import Flask
from flask_cors import CORS

from routes.survey           import survey_bp
from routes.clusters         import clusters_bp
from routes.result           import result_bp
from routes.vacancy_analysis import vacancy_analysis_bp
from routes.resume_analysis  import resume_analysis_bp
from routes.duplicates       import duplicates_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(survey_bp)
app.register_blueprint(clusters_bp)
app.register_blueprint(result_bp)
app.register_blueprint(vacancy_analysis_bp)
app.register_blueprint(resume_analysis_bp)
app.register_blueprint(duplicates_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
