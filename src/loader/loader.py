from io import StringIO
from typing import Literal

import pandas as pd
from sqlalchemy import create_engine


COPY_ESCAPES = str.maketrans({
    "\\": r"\\",
    "\t": r"\t",
    "\r": r"\r",
    "\n": r"\n",
})


def copy_value(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return r"\N"
    return str(value).translate(COPY_ESCAPES)


def psql_insert_copy(table, conn, keys, data_iter):
    preparer = conn.dialect.identifier_preparer
    table_name = preparer.format_table(table.table)
    columns = ", ".join(map(preparer.quote_identifier, keys))
    sql = f"COPY {table_name} ({columns}) FROM STDIN"

    with StringIO() as buffer:
        for row in data_iter:
            buffer.write("\t".join(map(copy_value, row)) + "\n")

        buffer.seek(0)
        with conn.connection.cursor() as cursor:
            cursor.copy_expert(sql, buffer)


class Loader:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, pool_pre_ping=True)

    def run(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: Literal["append", "replace", "fail"] = "replace",
        chunksize: int = 50_000,
    ) -> int:
        if df.empty:
            print(f"[{table_name}] Датафрейм пуст, пропуск загрузки.")
            return 0

        categories = df.select_dtypes(include="category").columns
        if len(categories):
            df = df.astype(dict.fromkeys(categories, str))

        df.to_sql(
            table_name,
            self.engine,
            if_exists=if_exists,
            index=False,
            chunksize=chunksize,
            method=psql_insert_copy,
        )

        print(f"[{table_name}] Успешно загружено {len(df)} строк.")
        return len(df)