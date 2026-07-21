import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

# Snowflake connection
engine = create_engine(
    f"snowflake://{os.getenv('user')}:{os.getenv('password')}"
    f"@{os.getenv('account')}/{os.getenv('database')}"
    f"/{os.getenv('schema')}?warehouse={os.getenv('warehouse')}"
)

dataset_path = Path("datasets")

for csv_file in dataset_path.glob("*.csv"):
    table_name = csv_file.stem.upper()      # employees.csv -> EMPLOYEES

    print(f"Loading {csv_file.name} -> {table_name}")

    df = pd.read_csv(csv_file)

    df.columns = (
        df.columns.str.strip()
                  .str.replace(" ", "_")
                  .str.upper()
    )

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",   # replace / append
        index=False,
        method="multi"
    )

print("All CSV files loaded successfully.")
