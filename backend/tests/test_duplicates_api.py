"""
Тесты API эндпоинта /api/duplicates.
"""

import unittest

from flask import Flask

from routes.duplicates import duplicates_bp


class DuplicatesAPITest(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(duplicates_bp)
        self.client = app.test_client()

    def test_endpoint_with_vacancies(self):
        payload = {
            "vacancies": [
                {"id": 1, "title": "Python Developer", "company": "ООО Тест", "description": "desc"},
                {"id": 2, "title": "Python Developer", "company": "ООО Тест", "description": "desc"},
            ],
            "threshold": 0.9,
        }
        resp = self.client.post("/api/duplicates", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("threshold", data)
        self.assertIn("pairs", data)
        self.assertIn("groups", data)
        self.assertEqual(data["vacancyCount"], 2)
        self.assertEqual(data["pairCount"], 1)

    def test_invalid_threshold_returns_400(self):
        payload = {"vacancies": [], "threshold": 2.0}
        resp = self.client.post("/api/duplicates", json=payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_vacancies_not_list_returns_400(self):
        payload = {"vacancies": "bad"}
        resp = self.client.post("/api/duplicates", json=payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_non_dict_body_returns_400(self):
        resp = self.client.post("/api/duplicates", json=[])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_default_threshold_used_when_missing(self):
        payload = {
            "vacancies": [
                {"id": 1, "title": "Python Developer", "company": "ООО Тест", "description": "A"},
                {"id": 2, "title": "Python Developer", "company": "ООО Тест", "description": "B"},
            ]
        }
        resp = self.client.post("/api/duplicates", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("threshold", data)
