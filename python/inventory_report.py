import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from db_connection import get_connection

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory Reports"]
)

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)


@router.get("/product/{product_name}")
def quantity_sold_by_product(product_name: str):
    """
    Retrieve quantity sold for a specific product using Product Name.
    """

    conn = get_connection()

    try:
        query = """
        SELECT
            P.PRODUCT_ID,
            P.PRODUCT_NAME,
            SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
            ON OI.PRODUCT_ID = P.PRODUCT_ID
        WHERE UPPER(P.PRODUCT_NAME) = UPPER(%s)
        GROUP BY
            P.PRODUCT_ID,
            P.PRODUCT_NAME;
        """

        df = pd.read_sql(query, conn, params=[product_name])

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No sales found for product '{product_name}'."
            )

        file_path = "output/quantity_sold_by_product.csv"
        df.to_csv(file_path, index=False)

        return {
            "message": "Quantity Sold by Product report generated successfully.",
            "csv_file": file_path,
            "data": df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


@router.get("/category/{category_name}")
def category_wise_quantity(category_name: str):
    """
    Retrieve quantity sold for a specific category.
    """

    conn = get_connection()

    try:
        query = """
        SELECT
            P.CATEGORY,
            SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
            ON OI.PRODUCT_ID = P.PRODUCT_ID
        WHERE UPPER(P.CATEGORY) = UPPER(%s)
        GROUP BY
            P.CATEGORY;
        """

        df = pd.read_sql(query, conn, params=[category_name])

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No sales found for category '{category_name}'."
            )

        file_path = "output/category_wise_quantity.csv"
        df.to_csv(file_path, index=False)

        return {
            "message": "Category-wise Quantity Sold report generated successfully.",
            "csv_file": file_path,
            "data": df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


@router.get("/top10")
def top_10_fast_moving_products():
    """
    Retrieve Top 10 Fast Moving Products.
    """

    conn = get_connection()

    try:
        query = """
        SELECT
            P.PRODUCT_ID,
            P.PRODUCT_NAME,
            SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
            ON OI.PRODUCT_ID = P.PRODUCT_ID
        GROUP BY
            P.PRODUCT_ID,
            P.PRODUCT_NAME
        ORDER BY
            TOTAL_SOLD DESC
        LIMIT 10;
        """

        df = pd.read_sql(query, conn)

        file_path = "output/top10_fast_moving_products.csv"
        df.to_csv(file_path, index=False)

        return {
            "message": "Top 10 Fast Moving Products report generated successfully.",
            "csv_file": file_path,
            "data": df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()