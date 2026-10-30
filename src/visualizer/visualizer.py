from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sqlalchemy import create_engine, text


class Visualizer:
    def __init__(self, db_url: str, output_dir: str | Path = "reports/figures"):
        self.engine = create_engine(db_url)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Настройки глобального стиля графиков
        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams["font.sans-serif"] = "DejaVu Sans"
        plt.rcParams["axes.unicode_minus"] = False

    def _save_or_show(self, filename: str) -> None:
        save_path = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"График сохранен: {save_path}")
        plt.close()

    def plot_score_distribution(self) -> None:
        """1. Гистограмма распределения score (с логарифмической шкалой)."""
        query = """
        SELECT score 
        FROM all_comments 
        WHERE score IS NOT NULL;
        """
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)

        plt.figure(figsize=(10, 6))
        # На Reddit score сильно скошен вправо: обрезаем крайние перцентили или используем log_scale
        sns.histplot(
            data=df,
            x="score",
            bins=60,
            log_scale=(False, True),  # Логарифм по оси Y (количеству), чтобы видеть редкие высокие значения
            color="#2b5c8f",
            edgecolor="black",
        )
        plt.title("Распределение оценок (Score) комментариев", fontsize=14, fontweight="bold")
        plt.xlabel("Score (Рейтинг)", fontsize=12)
        plt.ylabel("Количество комментариев (Log scale)", fontsize=12)

        self._save_or_show("01_score_distribution.png")

    def plot_hourly_activity(self) -> None:
        """2. Линейный график активности по часам суток (по сабреддитам)."""
        query = """
        SELECT subreddit_name_prefixed, hour, COUNT(*) AS comment_count
        FROM all_comments
        GROUP BY subreddit_name_prefixed, hour
        ORDER BY hour ASC;
        """
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)

        plt.figure(figsize=(12, 6))
        sns.lineplot(
            data=df,
            x="hour",
            y="comment_count",
            hue="subreddit_name_prefixed",
            marker="o",
            linewidth=2.5,
        )
        plt.title("Динамика активности пользователей по часам суток", fontsize=14, fontweight="bold")
        plt.xlabel("Час суток (UTC)", fontsize=12)
        plt.ylabel("Количество комментариев", fontsize=12)
        plt.xticks(range(0, 24))
        plt.legend(title="Сабреддит", bbox_to_anchor=(1.02, 1), loc="upper left")

        self._save_or_show("02_hourly_activity.png")

    def plot_day_hour_heatmap(self) -> None:
        """3. Heatmap: день недели × час комментария."""
        query = """
        SELECT day_of_week, hour, COUNT(*) AS comment_count
        FROM all_comments
        GROUP BY day_of_week, hour;
        """
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)

        # Сводная таблица (дни недели х часы)
        pivot = df.pivot(index="day_of_week", columns="hour", values="comment_count").fillna(0)

        # Замена числовых индексов дней недели на читаемые названия
        day_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        pivot.index = [day_labels[i] for i in pivot.index]

        plt.figure(figsize=(14, 6))
        sns.heatmap(
            pivot,
            cmap="YlGnBu",
            linewidths=0.5,
            cbar_kws={"label": "Число комментариев"},
        )
        plt.title("Тепловая карта активности: День недели × Час (UTC)", fontsize=14, fontweight="bold")
        plt.xlabel("Час суток", fontsize=12)
        plt.ylabel("День недели", fontsize=12)

        self._save_or_show("03_day_hour_heatmap.png")

    def plot_length_vs_score_scatter(self, sample_size: int = 15000) -> None:
        """4. Scatter plot: длина комментария vs. score."""
        # Для scatter plot берем срез данных (sample), чтобы не перегружать рендеринг миллионом точек
        query = f"""
        SELECT body_length, score, subreddit_name_prefixed
        FROM all_comments
        WHERE body_length <= 4000 AND score BETWEEN -50 AND 1000
        ORDER BY RANDOM()
        LIMIT {sample_size};
        """
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)

        plt.figure(figsize=(11, 7))
        sns.scatterplot(
            data=df,
            x="body_length",
            y="score",
            hue="subreddit_name_prefixed",
            alpha=0.4,
            edgecolor=None,
            s=25,
        )
        plt.title(f"Связь длины комментария и рейтинга (выборка: {sample_size:,} точек)", fontsize=14, fontweight="bold")
        plt.xlabel("Длина комментария (символов)", fontsize=12)
        plt.ylabel("Score (Рейтинг)", fontsize=12)
        plt.legend(title="Сабреддит", bbox_to_anchor=(1.02, 1), loc="upper left")

        self._save_or_show("04_length_vs_score_scatter.png")

    def plot_top_subreddits_bar(self, limit: int = 10) -> None:
        """5. Bar chart: топ сабреддитов по числу комментариев."""
        query = f"""
        SELECT subreddit_name_prefixed, COUNT(*) AS comment_count
        FROM all_comments
        GROUP BY subreddit_name_prefixed
        ORDER BY comment_count DESC
        LIMIT {limit};
        """
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)

        plt.figure(figsize=(10, 6))
        barplot = sns.barplot(
            data=df,
            x="comment_count",
            y="subreddit_name_prefixed",
            hue="subreddit_name_prefixed",
            legend=False,
            palette="Blues_r",
        )

        # Подписи числовых значений прямо на столбцах
        for p in barplot.patches:
            width = p.get_width()
            barplot.annotate(
                f"{int(width):,}",
                (width, p.get_y() + p.get_height() / 2.0),
                xytext=(6, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=10,
            )

        plt.title(f"Топ-{limit} сабреддитов по числу комментариев", fontsize=14, fontweight="bold")
        plt.xlabel("Количество комментариев", fontsize=12)
        plt.ylabel("Сабреддит", fontsize=12)
        plt.xlim(0, df["comment_count"].max() * 1.15)  # Запас места под подписи справа

        self._save_or_show("05_top_subreddits_bar.png")

    def run_all_plots(self) -> None:
        """Построение и сохранение всех требуемых графиков."""
        print("\n>>> Генерация графиков...")
        self.plot_score_distribution()
        self.plot_hourly_activity()
        self.plot_day_hour_heatmap()
        self.plot_length_vs_score_scatter()
        self.plot_top_subreddits_bar()
        print(">>> Все графики успешно сгенерированы в папку reports/figures/.")