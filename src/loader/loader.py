import io
from typing import Literal

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def psql_insert_copy(table, conn, keys, data_iter):
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = io.StringIO()
        for row in data_iter:
            clean_row = []
            for val in row:
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    clean_row.append(r"\N")
                else:
                    s_val = str(val)
                    s_val = (
                        s_val.replace("\\", "\\\\")
                        .replace("\t", "\\t")
                        .replace("\r", "\\r")
                        .replace("\n", "\\n")
                    )
                    clean_row.append(s_val)

            s_buf.write("\t".join(clean_row) + "\n")

        s_buf.seek(0)

        columns = ", ".join(f'"{k}"' for k in keys)
        table_name = (
            f'"{table.schema}"."{table.name}"'
            if table.schema
            else f'"{table.name}"'
        )
        sql = f"COPY {table_name} ({columns}) FROM STDIN WITH (FORMAT text, NULL '\\N')"
        cur.copy_expert(sql=sql, file=s_buf)


class Loader:
    def __init__(self, db_url: str):
        self.engine: Engine = create_engine(db_url, pool_pre_ping=True)

    def run(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: Literal["append", "replace", "fail"] = "replace",
        chunksize: int = 50000,
    ) -> int:
        if df.empty:
            print(f"[{table_name}] Датафрейм пуст, пропуск загрузки.")
            return 0

        upload_df = df.copy()
        for col in upload_df.select_dtypes(include=["category"]).columns:
            upload_df[col] = upload_df[col].astype(str)

        upload_df.to_sql(
            name=table_name,
            con=self.engine,
            if_exists=if_exists,
            index=False,
            chunksize=chunksize,
            method=psql_insert_copy,
        )

        rows_loaded = len(upload_df)
        print(f"[{table_name}] Успешно загружено {rows_loaded} строк.")
        return rows_loaded