import re
import ast
import textwrap
from abc import ABC, abstractmethod
from collections import Counter
from io import BytesIO
from typing import Dict, List, Optional
import base64
import traceback

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _try_import(name):
    try:
        import importlib
        return importlib.import_module(name)
    except ImportError:
        return None


class BaseGraphGenerator(ABC):
    def __init__(self, title: str, figsize: tuple = (10, 6)):
        self.title   = title
        self.figsize = figsize

    @abstractmethod
    def create_plot(self, data: pd.DataFrame) -> plt.Figure:
        pass

    def save_to_base64(self, fig: plt.Figure, dpi: int = 110) -> str:
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        buf.seek(0)
        result = base64.b64encode(buf.getvalue()).decode()
        plt.close(fig)
        return result

    def generate(self, data: pd.DataFrame) -> Optional[str]:
        """Возвращает base64 строку или None при ошибке."""
        try:
            fig = self.create_plot(data)
            return self.save_to_base64(fig)
        except Exception as e:
            print(f"[analytics] {self.__class__.__name__} failed: {e}")
            traceback.print_exc()
            return None


class RedFlagsDistributionGraph(BaseGraphGenerator):
    """Столбчатая диаграмма: распределение количества red flags."""

    def __init__(self):
        super().__init__("Распределение red flags", figsize=(9, 5))

    def create_plot(self, data: pd.DataFrame) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)

        if "red_flag_count" not in data.columns or data["red_flag_count"].isna().all():
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes, fontsize=14, color="#a0aec0")
            ax.set_title(self.title, fontsize=13, fontweight="bold")
            return fig

        counts = data["red_flag_count"].value_counts().sort_index()
        color_map = {0: "#48bb78", 1: "#ecc94b", 2: "#ecc94b",
                     3: "#ed8936", 4: "#ed8936"}
        colors = [color_map.get(v, "#e53e3e") for v in counts.index]

        bars = ax.bar(counts.index.astype(str), counts.values,
                      color=colors, edgecolor="white", linewidth=0.8)
        ax.set_title(self.title, fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Количество флагов", fontsize=11)
        ax.set_ylabel("Вакансий", fontsize=11)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)

        for bar, val in zip(bars, counts.values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    str(val), ha="center", va="bottom", fontsize=10)
        fig.tight_layout()
        return fig


class SkillsWordCloudGraph(BaseGraphGenerator):
    """Облако навыков кластера через WordCloud."""

    STOP = {
        "и", "в", "с", "по", "на", "для", "или", "из", "at", "of",
        "the", "and", "or", "to", "a", "an",
    }

    def __init__(self):
        super().__init__("Навыки кластера", figsize=(11, 6))

    def _parse_skills(self, data: pd.DataFrame) -> Counter:
        counter = Counter()
        for cell in data["key_skills"].dropna():
            try:
                parsed = ast.literal_eval(cell) if isinstance(cell, str) else cell
                if isinstance(parsed, list):
                    for skill in parsed:
                        s = str(skill).strip()
                        if s and s.lower() not in self.STOP and len(s) > 1:
                            counter[s] += 1
            except Exception:
                continue
        return counter

    def create_plot(self, data: pd.DataFrame) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)

        if "key_skills" not in data.columns:
            ax.text(0.5, 0.5, "Нет данных о навыках", ha="center", va="center",
                    transform=ax.transAxes, fontsize=13, color="#a0aec0")
            ax.set_title(self.title, fontsize=13, fontweight="bold")
            return fig

        counter = self._parse_skills(data)
        if not counter:
            ax.text(0.5, 0.5, "Навыки не указаны", ha="center", va="center",
                    transform=ax.transAxes, fontsize=13, color="#a0aec0")
            ax.set_title(self.title, fontsize=13, fontweight="bold")
            return fig

        try:
            from wordcloud import WordCloud
            wc = WordCloud(
                width=1000, height=540,
                background_color="white",
                colormap="Blues",
                max_words=80,
                prefer_horizontal=0.85,
                min_font_size=10,
            ).generate_from_frequencies(counter)
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
        except ImportError:
            top = counter.most_common(15)
            skills, counts = zip(*top)
            cmap = plt.cm.Blues_r
            colors = [cmap(0.3 + 0.5 * i / len(skills)) for i in range(len(skills))]
            ax.barh(range(len(skills)), counts, color=colors, edgecolor="white")
            ax.set_yticks(range(len(skills)))
            ax.set_yticklabels(skills, fontsize=10)
            ax.invert_yaxis()
            ax.set_xlabel("Упоминаний", fontsize=11)
            ax.grid(axis="x", alpha=0.3, linestyle="--")
            ax.spines[["top", "right"]].set_visible(False)

        ax.set_title(self.title, fontsize=13, fontweight="bold", pad=12)
        fig.tight_layout()
        return fig


class ExperienceDistributionGraph(BaseGraphGenerator):
    """Pie-chart: распределение по требуемому опыту."""

    EXP_MAP = {
        "noExperience": "Без опыта",
        "between1And3": "1–3 года",
        "between3And6": "3–6 лет",
        "moreThan6":    "6+ лет",
    }

    def __init__(self):
        super().__init__("Распределение по опыту", figsize=(7, 7))

    def create_plot(self, data: pd.DataFrame) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)

        if "experience_id" not in data.columns or data["experience_id"].isna().all():
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes, fontsize=13, color="#a0aec0")
            ax.set_title(self.title, fontsize=13, fontweight="bold")
            return fig

        counts = data["experience_id"].value_counts()
        labels = [self.EXP_MAP.get(e, e) for e in counts.index]
        colors = ["#3d68ea", "#68d391", "#ecc94b", "#fc8181"][:len(counts)]

        wedges, texts, autotexts = ax.pie(
            counts.values, labels=labels,
            autopct="%1.0f%%", colors=colors,
            startangle=90, pctdistance=0.75,
            wedgeprops={"linewidth": 2, "edgecolor": "white"},
        )
        for at in autotexts:
            at.set_fontsize(11)
            at.set_fontweight("bold")
            at.set_color("white")

        ax.set_title(self.title, fontsize=13, fontweight="bold", pad=12)
        fig.tight_layout()
        return fig


class RedFlagsTopBarGraph(BaseGraphGenerator):
    def __init__(self, top_n: int = 8):
        super().__init__("Топ красных флагов", figsize=(7, 5))
        self.top_n = top_n

    def create_plot(self, data: pd.DataFrame) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)

        if "red_flag" not in data.columns:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes, fontsize=13, color="#a0aec0")
            ax.set_title(self.title, fontsize=13, fontweight="bold")
            return fig

        all_flags: List[str] = []
        for cell in data["red_flag"].dropna():
            parts = [f.strip() for f in str(cell).split("⚠️") if f.strip()]
            all_flags.extend(parts)

        if not all_flags:
            ax.text(0.5, 0.5, "Красных флагов не обнаружено 🎉",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=13, color="#48bb78")
            ax.set_title(self.title, fontsize=13, fontweight="bold")
            return fig

        top = Counter(all_flags).most_common(self.top_n)
        labels = ["\n".join(textwrap.wrap(f, 35)) for f, _ in top]
        values = [c for _, c in top]
        colors = plt.cm.Reds(np.linspace(0.45, 0.85, len(values)))

        bars = ax.barh(range(len(labels)), values, color=colors, edgecolor="white")
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_title(self.title, fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Количество вакансий", fontsize=11)
        ax.grid(axis="x", alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=10)
        fig.tight_layout()
        return fig


class ClusterAnalyticsService:
    """Сервис генерации графиков"""

    def __init__(self):
        self.generators: Dict[str, BaseGraphGenerator] = {
            "flags_distribution":      RedFlagsDistributionGraph(),
            "top_skills":              SkillsWordCloudGraph(),
            "experience_distribution": ExperienceDistributionGraph(),
            "top_red_flags":           RedFlagsTopBarGraph(top_n=8),
        }

    def generate_all(self, data: pd.DataFrame,
                     needed_graphs: Optional[List[str]] = None) -> Dict[str, str]:
        graphs = needed_graphs or list(self.generators.keys())
        result = {}
        for name in graphs:
            if name not in self.generators:
                continue
            img = self.generators[name].generate(data)
            if img:
                result[f"{name}_plot"] = img
            else:
                print(f"[analytics] Skipping {name} — generate() returned None")
        return result
