"""
Загрузка датафрейма, модели SBERT и вспомогательных данных.
Все объекты загружаются один раз при старте приложения.
"""

import os
import json
import ast
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from data.cluster_data import CLUSTER_MAP, CLUSTER_INFO


for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if var in os.environ:
        os.environ.pop(var)
BASE_DIR = os.path.dirname(__file__)

LOCAL_MODEL_PATH = os.path.join(BASE_DIR, "sbert_model")

HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN

DF_PATH = os.path.join(BASE_DIR, "df_for_clasters.csv")
TOP_COMPANIES_PATH = os.path.join(BASE_DIR, "top_companies.csv")
SKILLS_PATH = os.path.join(BASE_DIR, "junior_it_skills.json")


def _load_df() -> pd.DataFrame:
    df = pd.read_csv(DF_PATH, encoding="utf-8")
    return df

df_for_clasters: pd.DataFrame = _load_df()


def _load_top_companies():
    top_df = pd.read_csv(TOP_COMPANIES_PATH)
    top10_set = set(top_df[top_df["Место"] <= 10]["Компания"])
    return [c.lower().strip() for c in top10_set]

top10: list = _load_top_companies()


def _load_skills() -> list:
    with open(SKILLS_PATH, "r", encoding="utf-8") as f:
        skills = json.load(f)
    return [s.lower() for s in skills]

JUNIOR_SKILLS: list = _load_skills()


if not os.path.exists(LOCAL_MODEL_PATH):
    raise FileNotFoundError(
        f"Модель SBERT не найдена по пути {LOCAL_MODEL_PATH}. "
        f"Скачайте модель через SentenceTransformer.save() заранее."
    )

_model = SentenceTransformer(LOCAL_MODEL_PATH)

_texts = [t[:500] for t in df_for_clasters["minimal_clean_text"].tolist()]
sbert_vec: np.ndarray = _model.encode(
    _texts,
    normalize_embeddings=True,
    batch_size=32,
    show_progress_bar=True,
)


# Вспомогательные функции
def detect_cluster(resume_text: str) -> int:
    """Определяет кластер по тексту резюме через косинусное сходство"""
    emb = _model.encode([resume_text], normalize_embeddings=True)
    similarities = (sbert_vec @ emb.T).flatten()
    idx = similarities.argmax()
    return int(df_for_clasters.iloc[idx]["labels_final"])


def detect_cluster_from_answers(tech: str, load: str, corporate: str) -> int:
    """Определяет кластер по ответам опроса через CLUSTER_MAP"""
    tech_map = {"low": "T_1", "medium": "T_2", "high": "T_3", "any": None}
    load_map = {"low": "O_1", "medium": "O_2", "high": "O_3", "any": None}
    corp_map = {"close": "F_1", "far": "F_0", "medium": None, "any": None}

    T = tech_map.get(tech)
    O = load_map.get(load)
    F = corp_map.get(corporate)

    if not T and not O and not F:
        return int(df_for_clasters.groupby("labels_final")["red_flag_count"].mean().idxmin())

    if F is None:
        for f_val in ("F_0", "F_1"):
            key = (T, O, f_val)
            if key in CLUSTER_MAP:
                return CLUSTER_MAP[key]

    key = (T, O, F)
    if key in CLUSTER_MAP:
        return CLUSTER_MAP[key]

    return int(df_for_clasters.groupby("labels_final")["red_flag_count"].mean().idxmin())


def get_cluster_vacancies(cluster_id: int) -> pd.DataFrame:
    return df_for_clasters[df_for_clasters["labels_final"] == cluster_id].head(100)


def extract_skills(text: str) -> list:
    if not text:
        return []
    text_lower = text.lower()
    return [skill for skill in JUNIOR_SKILLS if skill in text_lower]


def top_companies_list(cluster_df: pd.DataFrame) -> list:
    return cluster_df["employer_name"].value_counts().head(100).index.tolist()


def normalize_skill(s: str) -> str:
    return s.lower().strip()


def vacancy_has_skill(row, skills_lower: list) -> bool:
    if not skills_lower:
        return True

    raw = row.get("key_skills", "")
    try:
        ks_list  = ast.literal_eval(raw) if isinstance(raw, str) else (raw or [])
        ks_lower = [s.lower() for s in ks_list]
    except Exception:
        ks_lower = []

    for skill in skills_lower:
        if any(skill in ks for ks in ks_lower):
            return True

    text = str(row.get("minimal_clean_text", "")).lower()
    return any(skill in text for skill in skills_lower)
