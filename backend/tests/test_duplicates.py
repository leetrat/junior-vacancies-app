"""
Тесты обнаружения дубликатов вакансий (services/duplicate_detection.py).

Запуск из корня репозитория:
    python -m unittest discover -s backend/tests -v
или из каталога backend:
    python -m unittest discover -s tests -v
"""

import copy
import os
import sys
import unittest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.duplicate_detection import (  # noqa: E402
    DEFAULT_SIMILARITY_THRESHOLD,
    _validate_threshold,
    compare_vacancies,
    detect_duplicates,
    find_duplicate_groups,
    find_duplicate_pairs,
    get_default_threshold,
    normalize_text,
    text_similarity,
)

# --- фикстуры ---------------------------------------------------------------
# Вакансия в формате датасета (df_for_clasters.csv)
A1 = {
    "id": "101",
    "name": "Junior Python Developer",
    "employer_name": "ООО Ромашка",
    "description": "<p>Работа в команде разработки. <b>Python</b>, SQL, git.</p>",
}
# Тот же вакансия: другой id, другой регистр/форматирование
A2 = {
    "id": "102",
    "name": "  junior   PYTHON developer ",
    "employer_name": "ромашка",
    "description": "Работа в команде разработки. Python, SQL, git.",
}
# Та же компания и должность, но описание заметно отличается
B1 = {
    "id": "201",
    "title": "Middle Python Developer",
    "company": "Acme",
    "description": "Мы ищем разработчика на Python. Работа с API, тестами и данными.",
}
B2 = {
    "id": "202",
    "title": "Middle Python Developer",
    "company": "Acme",
    "description": "Мы ищем разработчика на Python. Работа с API, тестами, данными и документацией.",
}
# Та же должность и описание, но другая компания
C1 = {
    "id": "301",
    "title": "Junior Python Developer",
    "company": "Яндекс",
    "description": "Работа в команде разработки. Python, SQL, git.",
}
C2 = {
    "id": "302",
    "title": "Junior Python Developer",
    "company": "Авито",
    "description": "Работа в команде разработки. Python, SQL, git.",
}
# Похожее описание, но другая должность (одна и та же компания)
D1 = {
    "id": "401",
    "title": "Junior Python Developer",
    "company": "Acme",
    "description": "Работа в команде разработки. Python, SQL, git, code review, наставник.",
}
D2 = {
    "id": "402",
    "title": "Junior Sales Manager",
    "company": "Acme",
    "description": "Работа в команде разработки. Python, SQL, git, code review, наставник.",
}


class NormalizeTextTests(unittest.TestCase):
    def test_case_and_whitespace(self):
        self.assertEqual(normalize_text("  Junior   Python\tDeveloper\n"),
                         "junior python developer")

    def test_html_markup_removed(self):
        self.assertEqual(normalize_text("<p>Junior <b>Python</b> Developer</p>"),
                         "junior python developer")

    def test_punctuation_removed(self):
        self.assertEqual(normalize_text("C++ / C#"), "c c")

    def test_html_entities_unescaped(self):
        self.assertEqual(normalize_text("R&amp;D team"), "r d team")

    def test_empty_values(self):
        self.assertEqual(normalize_text(None), "")
        self.assertEqual(normalize_text(""), "")
        self.assertEqual(normalize_text(float("nan")), "")
        self.assertEqual(normalize_text([]), "")

    def test_non_string_values(self):
        self.assertEqual(normalize_text(12345), "12345")
        self.assertEqual(normalize_text(["Python", "SQL"]), "python sql")

    def test_text_similarity(self):
        self.assertEqual(text_similarity("Python  Developer", "python developer"), 1.0)
        self.assertEqual(text_similarity("", ""), 1.0)
        self.assertEqual(text_similarity("Python", ""), 0.0)
        self.assertLess(text_similarity("Python Developer", "Sales Manager"), 0.5)


class CompareVacanciesTests(unittest.TestCase):
    def test_exact_duplicate_despite_different_ids(self):
        result = compare_vacancies(A1, A2, threshold=DEFAULT_SIMILARITY_THRESHOLD)
        self.assertIsNotNone(result)
        self.assertEqual(result["matchType"], "exact")
        self.assertEqual(result["score"], 1.0)

    def test_similar_duplicate(self):
        result = compare_vacancies(B1, B2, threshold=DEFAULT_SIMILARITY_THRESHOLD)
        self.assertIsNotNone(result)
        self.assertEqual(result["matchType"], "similar")
        self.assertGreaterEqual(result["score"], DEFAULT_SIMILARITY_THRESHOLD)
        self.assertLess(result["score"], 1.0)

    def test_identical_titles_different_companies_not_duplicates(self):
        self.assertIsNone(
            compare_vacancies(C1, C2, threshold=DEFAULT_SIMILARITY_THRESHOLD))

    def test_similar_descriptions_different_positions_not_duplicates(self):
        self.assertIsNone(
            compare_vacancies(D1, D2, threshold=DEFAULT_SIMILARITY_THRESHOLD))

    def test_missing_description_one_side(self):
        no_description = {"id": "501", "title": "Middle Python Developer",
                          "company": "Acme"}
        with_description = dict(B1)
        result = compare_vacancies(no_description, with_description,
                                   threshold=DEFAULT_SIMILARITY_THRESHOLD)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result["score"], DEFAULT_SIMILARITY_THRESHOLD)

    def test_missing_title_or_company_not_comparable(self):
        no_title = {"id": "601", "company": "Acme", "description": "Python"}
        no_company = {"id": "602", "title": "Python Developer",
                      "description": "Python"}
        self.assertIsNone(compare_vacancies(no_title, A1))
        self.assertIsNone(compare_vacancies(no_company, A1))
        self.assertIsNone(compare_vacancies(no_title, no_company))

    def test_company_legal_form_variants_are_same_company(self):
        left = {"id": "701", "title": "Python Developer",
                "company": "ООО Ромашка"}
        right = {"id": "702", "title": "Python Developer",
                 "company": "Ромашка"}
        result = compare_vacancies(left, right)
        self.assertIsNotNone(result)

    def test_non_dict_entries_return_none(self):
        self.assertIsNone(compare_vacancies("garbage", A1))
        self.assertIsNone(compare_vacancies(A1, None))

    def test_threshold_must_be_valid(self):
        for bad in (0, -0.5, 1.5, "abc", True, float("nan")):
            with self.assertRaises(ValueError, msg=f"threshold={bad!r}"):
                _validate_threshold(bad)
        self.assertEqual(_validate_threshold(0.85), 0.85)
        self.assertEqual(_validate_threshold(1), 1.0)


class FindDuplicatesTests(unittest.TestCase):
    def test_empty_dataset(self):
        result = detect_duplicates([])
        self.assertEqual(result["vacancyCount"], 0)
        self.assertEqual(result["pairCount"], 0)
        self.assertEqual(result["groupCount"], 0)
        self.assertEqual(result["pairs"], [])
        self.assertEqual(result["groups"], [])

    def test_single_vacancy(self):
        result = detect_duplicates([A1])
        self.assertEqual(result["vacancyCount"], 1)
        self.assertEqual(result["pairs"], [])
        self.assertEqual(result["groups"], [])

    def test_pair_returned_with_ids_and_score(self):
        pairs = find_duplicate_pairs([A1, A2])
        self.assertEqual(len(pairs), 1)
        pair = pairs[0]
        self.assertEqual({pair["idA"], pair["idB"]}, {"101", "102"})
        self.assertEqual(pair["matchType"], "exact")
        self.assertEqual(pair["score"], 1.0)

    def test_identical_titles_different_companies_no_pairs(self):
        self.assertEqual(find_duplicate_pairs([C1, C2]), [])

    def test_similar_descriptions_different_positions_no_pairs(self):
        self.assertEqual(find_duplicate_pairs([D1, D2]), [])

    def test_similar_vacancies_detected_with_default_threshold(self):
        pairs = find_duplicate_pairs([B1, B2])
        self.assertEqual(len(pairs), 1)
        self.assertGreaterEqual(pairs[0]["score"], DEFAULT_SIMILARITY_THRESHOLD)

    def test_missing_fields_do_not_crash(self):
        vacancies = [
            {"id": "1", "name": None, "employer_name": float("nan"),
             "description": None},
            {"id": "2"},
            {"id": "3", "name": "", "employer_name": "",
             "description": "какой-то текст"},
            A1, A2,
        ]
        pairs = find_duplicate_pairs(vacancies)
        self.assertEqual(len(pairs), 1)  # только A1/A2

    def test_ids_generated_when_missing(self):
        first = {"title": "Python Developer", "company": "Acme",
                 "description": "Описание вакансии"}
        second = {"title": "python developer", "company": "acme",
                  "description": "Описание вакансии"}
        pairs = find_duplicate_pairs([first, second])
        self.assertEqual(len(pairs), 1)
        self.assertEqual({pairs[0]["idA"], pairs[0]["idB"]}, {"#0", "#1"})

    def test_non_dict_entries_are_skipped(self):
        self.assertEqual(find_duplicate_pairs(["junk", None, 42]), [])

    def test_group_of_three_records(self):
        third = dict(A2, id="103")
        groups = find_duplicate_groups([A1, A2, third])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["ids"], ["101", "102", "103"])
        self.assertEqual(groups[0]["size"], 3)
        self.assertEqual(groups[0]["score"], 1.0)
        self.assertEqual(len(find_duplicate_pairs([A1, A2, third])), 3)

    def test_two_separate_groups(self):
        other_pair = [
            {"id": "901", "title": "Go Developer", "company": "Acme",
             "description": "Разработка сервисов на Go"},
            {"id": "902", "title": "go developer", "company": "acme",
             "description": "Разработка сервисов на Go"},
        ]
        result = detect_duplicates([A1, A2] + other_pair)
        self.assertEqual(result["pairCount"], 2)
        self.assertEqual(result["groupCount"], 2)
        sizes = sorted(g["size"] for g in result["groups"])
        self.assertEqual(sizes, [2, 2])


class ThresholdTests(unittest.TestCase):
    def test_score_exactly_equal_to_threshold_is_duplicate(self):
        # У идентичных вакансий score == 1.0; при пороге 1.0 они остаются дублями
        pairs = find_duplicate_pairs([A1, A2], threshold=1.0)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["score"], 1.0)

    def test_strict_threshold_rejects_similar_pair(self):
        self.assertLess(DEFAULT_SIMILARITY_THRESHOLD, 1.0)
        self.assertEqual(find_duplicate_pairs([B1, B2], threshold=1.0), [])

    def test_lower_threshold_detects_less_obvious_pair(self):
        # Одинаковые должность и компания, но разные описания:
        # score заметно ниже стандартного порога, но выше пониженного.
        same_title_a = {"id": "a", "title": "Python Developer",
                        "company": "Acme",
                        "description": "Разработка frontend интерфейсов на React"}
        same_title_b = {"id": "b", "title": "Python Developer",
                        "company": "Acme",
                        "description": "Поддержка серверной инфраструктуры Linux"}
        self.assertEqual(
            find_duplicate_pairs([same_title_a, same_title_b],
                                 threshold=DEFAULT_SIMILARITY_THRESHOLD), [])
        pairs = find_duplicate_pairs([same_title_a, same_title_b], threshold=0.6)
        self.assertEqual(len(pairs), 1)
        self.assertGreaterEqual(pairs[0]["score"], 0.6)

    def test_threshold_from_environment_variable(self):
        old = os.getenv("DUPLICATE_SIMILARITY_THRESHOLD")
        os.environ["DUPLICATE_SIMILARITY_THRESHOLD"] = "0.6"
        self.addCleanup(self._restore_env, old)
        self.assertEqual(get_default_threshold(), 0.6)
        # С порогом по умолчанию (из окружения) пара обнаруживается
        vacancies = [
            {"id": "a", "title": "Python Developer", "company": "Acme",
             "description": "Разработка frontend интерфейсов на React"},
            {"id": "b", "title": "Python Developer", "company": "Acme",
             "description": "Поддержка серверной инфраструктуры Linux"},
        ]
        result = detect_duplicates(vacancies)
        self.assertEqual(result["threshold"], 0.6)
        self.assertEqual(result["pairCount"], 1)

    def test_invalid_environment_value_falls_back_to_default(self):
        old = os.getenv("DUPLICATE_SIMILARITY_THRESHOLD")
        os.environ["DUPLICATE_SIMILARITY_THRESHOLD"] = "not-a-number"
        self.addCleanup(self._restore_env, old)
        self.assertEqual(get_default_threshold(), DEFAULT_SIMILARITY_THRESHOLD)

    @staticmethod
    def _restore_env(old):
        if old is None:
            os.environ.pop("DUPLICATE_SIMILARITY_THRESHOLD", None)
        else:
            os.environ["DUPLICATE_SIMILARITY_THRESHOLD"] = old


class OriginalDataTests(unittest.TestCase):
    def test_detection_does_not_modify_input(self):
        vacancies = [copy.deepcopy(A1), copy.deepcopy(A2), copy.deepcopy(B1),
                     copy.deepcopy(B2)]
        before = copy.deepcopy(vacancies)
        detect_duplicates(vacancies)
        self.assertEqual(vacancies, before)

    def test_compare_does_not_modify_input(self):
        left, right = copy.deepcopy(A1), copy.deepcopy(A2)
        before = copy.deepcopy([left, right])
        compare_vacancies(left, right)
        self.assertEqual([left, right], before)


if __name__ == "__main__":
    unittest.main()
