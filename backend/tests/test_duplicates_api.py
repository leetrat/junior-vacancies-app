"""
Тесты эндпоинта POST /api/duplicates (routes/duplicates.py).

Запускаются только при установленном Flask (в dev-окружении).
"""

import importlib.util
import os
import sys
import unittest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

FLASK_AVAILABLE = importlib.util.find_spec("flask") is not None

if FLASK_AVAILABLE:
    from flask import Flask
    from routes.duplicates import duplicates_bp


@unittest.skipUnless(FLASK_AVAILABLE, "Flask не установлен")
class DuplicatesApiTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(duplicates_bp)
        self.client = app.test_client()
        self.vacancies = [
            {"id": "101", "title": "Junior Python Developer",
             "company": "ООО Ромашка",
             "description": "Работа в команде. Python, SQL, git."},
            {"id": "102", "title": "junior python developer",
             "company": "Ромашка",
             "description": "Работа в команде. Python, SQL, git!"},
            {"id": "103", "title": "Junior Python Developer",
             "company": "Авито",
             "description": "Работа в команде. Python, SQL, git."},
        ]

    def test_returns_pairs_and_groups(self):
        response = self.client.post("/api/duplicates",
                                    json={"vacancies": self.vacancies})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["vacancyCount"], 3)
        self.assertEqual(payload["threshold"], 0.85)
        self.assertEqual(payload["pairCount"], 1)
        self.assertEqual(payload["groupCount"], 1)
        pair = payload["pairs"][0]
        self.assertEqual({pair["idA"], pair["idB"]}, {"101", "102"})
        self.assertEqual(pair["matchType"], "exact")
        self.assertEqual(payload["groups"][0]["ids"], ["101", "102"])

    def test_custom_threshold_is_applied(self):
        similar = [
            {"id": "201", "title": "Middle Python Developer",
             "company": "Acme",
             "description": "Мы ищем разработчика на Python. Работа с API и тестами."},
            {"id": "202", "title": "Middle Python Developer",
             "company": "Acme",
             "description": "Мы ищем разработчика на Python. Работа с API, тестами и документацией."},
        ]
        response = self.client.post(
            "/api/duplicates",
            json={"vacancies": similar, "threshold": 0.99},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["threshold"], 0.99)
        self.assertEqual(payload["pairCount"], 0)  # 0.99 строже схожести пары

        response = self.client.post("/api/duplicates",
                                    json={"vacancies": similar})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["threshold"], 0.85)
        self.assertEqual(payload["pairCount"], 1)
        self.assertEqual(payload["pairs"][0]["matchType"], "similar")

    def test_empty_vacancy_list(self):
        response = self.client.post("/api/duplicates", json={"vacancies": []})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["vacancyCount"], 0)
        self.assertEqual(payload["pairs"], [])
        self.assertEqual(payload["groups"], [])

    def test_invalid_threshold_returns_400(self):
        for bad in ("abc", 5, 0, -1):
            response = self.client.post(
                "/api/duplicates",
                json={"vacancies": [], "threshold": bad},
            )
            self.assertEqual(response.status_code, 400, msg=f"threshold={bad!r}")
            self.assertIn("error", response.get_json())

    def test_vacancies_must_be_a_list(self):
        response = self.client.post("/api/duplicates",
                                    json={"vacancies": {"id": "1"}})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_body_must_be_json_object(self):
        response = self.client.post("/api/duplicates", json=[1, 2, 3])
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
