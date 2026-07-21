from db_connection import get_connection

conn = get_connection()
cur = conn.cursor()

queries = {
    "Quantity Sold By Product":
        """
        SELECT P.PRODUCT_NAME,
               SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
        ON OI.PRODUCT_ID=P.PRODUCT_ID
        GROUP BY P.PRODUCT_NAME
        ORDER BY TOTAL_SOLD DESC;
        """,

    "Category-wise Quantity Sold":
        """
        SELECT P.CATEGORY,
               SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
        ON OI.PRODUCT_ID=P.PRODUCT_ID
        GROUP BY P.CATEGORY
        ORDER BY TOTAL_SOLD DESC;
        """,

    "Top 10 Fast Moving Products":
        """
        SELECT P.PRODUCT_NAME,
               SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
        ON OI.PRODUCT_ID=P.PRODUCT_ID
        GROUP BY P.PRODUCT_NAME
        ORDER BY TOTAL_SOLD DESC
        LIMIT 10;
        """
}

for title, sql in queries.items():
    print("\n", "="*50)
    print(title)
    print("="*50)
    cur.execute(sql)

    for row in cur.fetchall():
        print(row)

cur.close()
conn.close()