import os
import pandas as pd
from db_connection import get_connection

# Create output folder if it doesn't exist
os.makedirs("output", exist_ok=True)

conn = get_connection()

queries = {
    "quantity_sold_by_product": """
        SELECT P.PRODUCT_NAME,
               SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
          ON OI.PRODUCT_ID = P.PRODUCT_ID
        GROUP BY P.PRODUCT_NAME
        ORDER BY TOTAL_SOLD DESC;
    """,

    "category_wise_quantity_sold": """
        SELECT P.CATEGORY,
               SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
          ON OI.PRODUCT_ID = P.PRODUCT_ID
        GROUP BY P.CATEGORY
        ORDER BY TOTAL_SOLD DESC;
    """,

    "top_10_fast_moving_products": """
        SELECT P.PRODUCT_NAME,
               SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
          ON OI.PRODUCT_ID = P.PRODUCT_ID
        GROUP BY P.PRODUCT_NAME
        ORDER BY TOTAL_SOLD DESC
        LIMIT 10;
    """
}

for report_name, query in queries.items():
    df = pd.read_sql(query, conn)

    file_path = f"output/{report_name}.csv"
    df.to_csv(file_path, index=False)

    print(f"✅ {report_name} exported to {file_path}")

conn.close()
print("\nAll inventory reports exported successfully.")