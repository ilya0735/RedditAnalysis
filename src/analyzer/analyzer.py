import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class Analyzer:
    def __init__(self, db_url: str):
        self.engine: Engine = create_engine(db_url)

    def prepare_view(self, tables: list[str], view_name: str = "all_comments") -> None:
        if not tables:
            print("Список таблиц пуст, представление не создано.")
            return

        union_queries = [f"SELECT * FROM {table}" for table in tables]
        sql = f"""
        CREATE OR REPLACE VIEW {view_name} AS
        {" UNION ALL ".join(union_queries)};
        """
        with self.engine.begin() as conn:
            conn.execute(text(sql))
        print(f"Представление '{view_name}' успешно создано/обновлено для таблиц: {', '.join(tables)}.")

    def run_query(self, query: str) -> pd.DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(query), conn)

    def get_peak_hours(self) -> pd.DataFrame:
        """1. Час пик для каждого сабреддита."""
        query = """
        WITH hourly_counts AS (
            SELECT 
                subreddit_name_prefixed,
                hour,
                COUNT(*) AS total_comments,
                DENSE_RANK() OVER (
                    PARTITION BY subreddit_name_prefixed 
                    ORDER BY COUNT(*) DESC
                ) AS rank_pos
            FROM all_comments
            GROUP BY subreddit_name_prefixed, hour
        )
        SELECT 
            subreddit_name_prefixed,
            hour AS peak_hour,
            total_comments
        FROM hourly_counts
        WHERE rank_pos = 1
        ORDER BY subreddit_name_prefixed;
        """
        return self.run_query(query)

    def get_top_scored_comments(self, limit: int = 10) -> pd.DataFrame:
        """2. Топ-10 самых залайканных комментариев."""
        query = f"""
        SELECT 
            id,
            subreddit_name_prefixed,
            author,
            score,
            body_length,
            LEFT(body, 120) AS short_body
        FROM all_comments
        WHERE deleted = FALSE
        ORDER BY score DESC
        LIMIT {limit};
        """
        return self.run_query(query)

    def get_top_active_authors(self, limit: int = 20) -> pd.DataFrame:
        """3. Топ-20 самых активных авторов."""
        query = f"""
        SELECT 
            author,
            COUNT(*) AS total_comments,
            SUM(score) AS total_score,
            ROUND(AVG(score), 2) AS avg_score
        FROM all_comments
        WHERE author IS NOT NULL 
          AND author != '[deleted]'
        GROUP BY author
        ORDER BY total_comments DESC
        LIMIT {limit};
        """
        return self.run_query(query)

    def get_top_discussed_threads(self, limit: int = 20) -> pd.DataFrame:
        """4. Топ-20 самых обсуждаемых тредов (по link_id)."""
        query = f"""
        SELECT 
            link_id,
            subreddit_name_prefixed,
            COUNT(*) AS comment_count,
            ROUND(AVG(score), 2) AS avg_thread_score
        FROM all_comments
        GROUP BY link_id, subreddit_name_prefixed
        ORDER BY comment_count DESC
        LIMIT {limit};
        """
        return self.run_query(query)

    def get_avg_score_by_day(self) -> pd.DataFrame:
        """5. Средний score по дням недели."""
        query = """
        SELECT 
            day_of_week,
            CASE day_of_week
                WHEN 0 THEN 'Понедельник'
                WHEN 1 THEN 'Вторник'
                WHEN 2 THEN 'Среда'
                WHEN 3 THEN 'Четверг'
                WHEN 4 THEN 'Пятница'
                WHEN 5 THEN 'Суббота'
                WHEN 6 THEN 'Воскресенье'
            END AS day_name,
            COUNT(*) AS total_comments,
            ROUND(AVG(score), 2) AS avg_score
        FROM all_comments
        GROUP BY day_of_week
        ORDER BY day_of_week ASC;
        """
        return self.run_query(query)

    def get_longest_lived_threads(self, limit: int = 20) -> pd.DataFrame:
        """6. Долгоживущие треды (по времени между первым и последним комментарием)."""
        query = f"""
        SELECT 
            link_id,
            subreddit_name_prefixed,
            COUNT(*) AS comments_count,
            MIN(created_utc) AS first_comment_time,
            MAX(created_utc) AS last_comment_time,
            MAX(created_utc) - MIN(created_utc) AS thread_lifetime
        FROM all_comments
        GROUP BY link_id, subreddit_name_prefixed
        HAVING COUNT(*) > 5
        ORDER BY thread_lifetime DESC
        LIMIT {limit};
        """
        return self.run_query(query)

    def get_authors_comment_breakdown(self, limit: int = 20) -> pd.DataFrame:
        """7. Пользователи с наибольшим числом комментариев (распределение по длине)."""
        query = f"""
        SELECT 
            author,
            COUNT(*) AS total_comments,
            COUNT(*) FILTER (WHERE length_category = 'короткие') AS short_comments,
            COUNT(*) FILTER (WHERE length_category = 'средние') AS medium_comments,
            COUNT(*) FILTER (WHERE length_category = 'длинные') AS long_comments
        FROM all_comments
        WHERE author IS NOT NULL 
          AND author != '[deleted]'
        GROUP BY author
        ORDER BY total_comments DESC
        LIMIT {limit};
        """
        return self.run_query(query)

    def run_all_analysis(self) -> None:
        """Запуск всех аналитических отчетов и вывод в консоль."""
        tasks = [
            ("«Час пик» для каждого сабреддита", self.get_peak_hours),
            ("Топ-10 самых залайканных комментариев", self.get_top_scored_comments),
            ("Топ-20 самых активных авторов", self.get_top_active_authors),
            ("Топ-20 самых обсуждаемых тредов", self.get_top_discussed_threads),
            ("Средний score по дням недели", self.get_avg_score_by_day),
            ("«Долгоживущие» треды", self.get_longest_lived_threads),
            ("Пользователи с наибольшим числом комментариев", self.get_authors_comment_breakdown),
        ]

        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)

        for title, func in tasks:
            print("\n" + "=" * 80)
            print(f" ОТЧЕТ: {title}")
            print("=" * 80)
            df_result = func()
            print(df_result)