"""
Тесты логики детекции дубликатов вакансий.
"""

import os
import unittest

from services.duplicate_detection import (
    compare_vacancies,
    detect_duplicates,
    find_duplicate_pairs,
    find_duplicate_groups,
    get_default_threshold,
    normalize_company,
    normalize_text,
    text_similarity,
)


class DuplicateDetectionLogicTest(unittest.TestCase):
    def test_normalize_text_case_and_whitespace(self):
        self.assertEqual(normalize_text("Java Developer"), "java developer")
        self.assertEqual(normalize_text("  Java   Developer  "), "java developer")

    def test_normalize_text_punctuation_and_html(self):
        self.assertEqual(normalize_text("<p>Java, Developer!</p>"), "java developer")
        self.assertEqual(normalize_text("Junior&nbsp;Python"), "junior python")

    def test_normalize_company_strips_legal_forms(self):
        self.assertEqual(normalize_company("ООО Ромашка"), "ромашка")
        self.assertEqual(normalize_company("ООО \"Ромашка\""), "ромашка")
        self.assertEqual(normalize_company("LLC Example Ltd"), "example")

    def test_exact_duplicate_detected(self):
        v1 = {
            "id": 1,
            "title": "Python Developer",
            "company": "ООО Тест",
            "description": "Требуется разработка на Python",
        }
        v2 = dict(v1, id=2)
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["vacancyCount"], 2)
        self.assertEqual(res["pairCount"], 1)
        self.assertEqual(res["pairs"][0]["matchType"], "exact")
        self.assertAlmostEqual(res["pairs"][0]["score"], 1.0, places=2)

    def test_similar_descriptions_formatting(self):
        v1 = {
            "id": 1,
            "title": "Python Developer",
            "company": "ООО Тест",
            "description": "<p>Разработка бэкенда на Python и FastAPI.</p>",
        }
        v2 = {
            "id": 2,
            "title": "Python Developer",
            "company": "ООО Тест",
            "description": "Разработка бэкенда на Python и FastAPI",
        }
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 1)
        self.assertEqual(res["pairs"][0]["matchType"], "exact")

    def test_similar_but_not_exact(self):
        v1 = {
            "id": 1,
            "title": "Python Developer",
            "company": "ООО Тест",
            "description": "Разработка бэкенда",
        }
        v2 = {
            "id": 2,
            "title": "Python Developer",
            "company": "ООО Тест",
            "description": "Разработка web-приложений",
        }
        res = detect_duplicates([v1, v2], threshold=0.5)
        self.assertEqual(res["pairCount"], 1)
        self.assertTrue(res["pairs"][0]["score"] < 1.0)
        self.assertEqual(res["pairs"][0]["matchType"], "similar")

    def test_same_title_different_company_no_duplicate(self):
        v1 = {"id": 1, "title": "Python Developer", "company": "ООО А"}
        v2 = {"id": 2, "title": "Python Developer", "company": "ООО Б"}
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 0)

    def test_missing_title_skips(self):
        v1 = {"id": 1, "company": "ООО Тест", "description": "текст"}
        v2 = {"id": 2, "title": "Python", "company": "ООО Тест"}
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 0)

    def test_missing_company_skips(self):
        v1 = {"id": 1, "title": "Python Developer"}
        v2 = {"id": 2, "title": "Python Developer"}
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 0)

    def test_missing_description_uses_title_only(self):
        v1 = {"id": 1, "title": "Python Developer", "company": "ООО Тест"}
        v2 = {"id": 2, "title": "Python Developer", "company": "ООО Тест"}
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 1)
        self.assertIsNone(res["pairs"][0]["descriptionSimilarity"])

    def test_different_positions_similar_description_not_dupe(self):
        v1 = {"id": 1, "title": "Python Developer", "company": "ООО Тест", "description": "Python SQL REST"}
        v2 = {"id": 2, "title": "Data Analyst", "company": "ООО Тест", "description": "Python SQL REST"}
        res = detect_duplicates([v1, v2], threshold=0.85)
        self.assertEqual(res["pairCount"], 0)

    def test_identical_records_different_ids(self):
        v1 = {"id": "A", "title": "Python Developer", "company": "ООО Тест", "description": "descr"}
        v2 = {"id": "B", "title": "Python Developer", "company": "ООО Тест", "description": "descr"}
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 1)
        self.assertEqual(res["pairs"][0]["matchType"], "exact")

    def test_multiple_records_form_group(self):
        v1 = {"id": 1, "title": "Python Developer", "company": "ООО Тест", "description": "desc1"}
        v2 = {"id": 2, "title": "Python Developer", "company": "ООО Тест", "description": "desc1 very similar"}
        v3 = {"id": 3, "title": "Python Developer", "company": "ООО Тест", "description": "desc1 similar"}
        # connect via transitivity: v1-v2, v2-v3
        res = detect_duplicates([v1, v2, v3], threshold=0.8)
        self.assertTrue(res["pairCount"] >= 2)
        self.assertEqual(res["groupCount"], 1)
        self.assertEqual(res["groups"][0]["size"], 3)

    def test_threshold_exact_equality_counts(self):
        v1 = {"id": 1, "title": "Python Developer", "company": "ООО Тест"}
        v2 = {"id": 2, "title": "Python Developers", "company": "ООО Тест"}
        # compute exact
        c = compare_vacancies(v1, v2, threshold=1.0)
        score = c["score"] if c else text_similarity(v1["title"], v2["title"])
        res = detect_duplicates([v1, v2], threshold=score)
        self.assertEqual(res["pairCount"], 1)

    def test_configurable_threshold(self):
        v1 = {"id": 1, "title": "Python Developer", "company": "ООО Тест", "description": "А"}
        v2 = {"id": 2, "title": "Python Developer", "company": "ООО Тест", "description": "Б"}
        # with high threshold, maybe no
        res_high = detect_duplicates([v1, v2], threshold=0.95)
        res_low = detect_duplicates([v1, v2], threshold=0.5)
        self.assertTrue(res_high["pairCount"] <= res_low["pairCount"])

    def test_empty_dataset(self):
        res = detect_duplicates([])
        self.assertEqual(res["vacancyCount"], 0)
        self.assertEqual(res["pairCount"], 0)
        self.assertEqual(res["groupCount"], 0)

    def test_single_vacancy_no_pairs(self):
        res = detect_duplicates([{"id": 1, "title": "T", "company": "C"}])
        self.assertEqual(res["pairCount"], 0)
        self.assertEqual(res["groupCount"], 0)

    def test_input_not_modified(self):
        v1 = {"id": 1, "title": "Python Developer", "company": "ООО Тест"}
        v2 = {"id": 2, "title": "Python Developer", "company": "ООО Тест"}
        v1_before = dict(v1)
        v2_before = dict(v2)
        detect_duplicates([v1, v2])
        self.assertEqual(v1, v1_before)
        self.assertEqual(v2, v2_before)

    def test_env_threshold(self):
        old = os.environ.get("DUPLICATE_SIMILARITY_THRESHOLD")
        try:
            os.environ["DUPLICATE_SIMILARITY_THRESHOLD"] = "0.9"
            self.assertAlmostEqual(get_default_threshold(), 0.9)
            os.environ["DUPLICATE_SIMILARITY_THRESHOLD"] = "1.5"
            self.assertAlmostEqual(get_default_threshold(), 0.85)
        finally:
            if old is not None:
                os.environ["DUPLICATE_SIMILARITY_THRESHOLD"] = old
            else:
                os.environ.pop("DUPLICATE_SIMILARITY_THRESHOLD", None)

    def test_aliases_supported(self):
        v1 = {"name": "Python Developer", "employer_name": "ООО Тест", "minimal_clean_text": "desc"}
        v2 = {"title": "Python Developer", "company": "ООО Тест", "description": "desc"}
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 1)
        self.assertEqual(res["pairs"][0]["matchType"], "exact")

    def test_find_groups_handles_multiple_pairs(self):
        pairs = [
            {"idA": "1", "idB": "2", "score": 0.9},
            {"idA": "2", "idB": "3", "score": 0.8},
        ]
        groups = find_duplicate_groups(pairs)
        self.assertEqual(groups[0]["size"], 3)

    def test_invalid_threshold_raises(self):
        v1 = {"id": 1, "title": "T", "company": "C"}
        v2 = {"id": 2, "title": "T", "company": "C"}
        with self.assertRaises(ValueError):
            detect_duplicates([v1, v2], threshold=1.5)
        with self.assertRaises(ValueError):
            detect_duplicates([v1, v2], threshold=-0.1)
        with self.assertRaises(ValueError):
            detect_duplicates([v1, v2], threshold=True)
        with self.assertRaises(ValueError):
            detect_duplicates([v1, v2], threshold="high")

    def test_accepts_employer_dict(self):
        v1 = {"title": "Python", "employer": {"name": "ООО Тест"}, "description": "d"}
        v2 = {"title": "Python", "company": "ООО Тест", "description": "d"}
        res = detect_duplicates([v1, v2])
        self.assertEqual(res["pairCount"], 1)
