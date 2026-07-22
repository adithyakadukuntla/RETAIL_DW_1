from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from db_connection import get_connection
import pandas as pd
import os
import base64
import matplotlib.pyplot as plt

app = FastAPI(
    title="Payment Reports API",
    description="Swagger APIs for payment reports, pie charts, and highest revenue product",
    version="1.0"
)

REPORT_FOLDER = "../reports/payments"
os.makedirs(REPORT_FOLDER, exist_ok=True)


# =====================================
# HELPER: RENDER CHART AS HTML PAGE
# =====================================

def render_chart_html(chart_file: str, title: str) -> str:
    """
    Reads a PNG chart file, base64-encodes it, and returns a
    self-contained HTML page that displays the image inline
    (instead of triggering a file download).
    """
    with open(chart_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>{title}</title>
        </head>
        <body style="text-align:center; font-family:Arial, sans-serif; margin-top:40px;">
            <h2>{title}</h2>
            <img src="data:image/png;base64,{encoded}"
                 style="max-width:90%; height:auto; border:1px solid #ddd; border-radius:8px; padding:8px;" />
        </body>
    </html>
    """
    return html_content


# =====================================
# HOME API
# =====================================

@app.get("/")
def home():
    return {
        "message": "Payment Reports API is running",
        "swagger_url": "http://127.0.0.1:8000/docs"
    }


# =====================================
# 1. GET PAYMENT MODES
# =====================================

@app.get("/payment-modes")
def get_payment_modes():
    conn = get_connection()

    query = """
    SELECT DISTINCT PAYMENT_MODE
    FROM ORDERS
    ORDER BY PAYMENT_MODE
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return {
        "payment_modes": df["PAYMENT_MODE"].tolist()
    }


# =====================================
# 2. REVENUE BY PAYMENT MODE
# Use payment_mode = all for all modes
# Example:
# /revenue-by-payment-mode/all
# /revenue-by-payment-mode/Cash
# =====================================

@app.get("/revenue-by-payment-mode/{payment_mode}")
def revenue_by_payment_mode(payment_mode: str):

    conn = get_connection()

    if payment_mode.lower() == "all":

        query = """
        SELECT PAYMENT_MODE,
               SUM(NET_AMOUNT) AS TOTAL_REVENUE
        FROM ORDERS
        WHERE ORDER_STATUS = 'Delivered'
        GROUP BY PAYMENT_MODE
        ORDER BY TOTAL_REVENUE DESC
        """

        chart_title = "Revenue By All Payment Modes"

    else:

        query = f"""
        SELECT PAYMENT_MODE,
               SUM(NET_AMOUNT) AS TOTAL_REVENUE
        FROM ORDERS
        WHERE ORDER_STATUS = 'Delivered'
          AND PAYMENT_MODE = '{payment_mode}'
        GROUP BY PAYMENT_MODE
        """

        chart_title = f"Revenue By {payment_mode}"

    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No revenue data found"
        )

    csv_file = f"{REPORT_FOLDER}/revenue_by_payment_mode.csv"
    df.to_csv(csv_file, index=False)

    chart_file = f"{REPORT_FOLDER}/revenue_by_payment_mode_piechart.png"

    plt.figure(figsize=(8, 8))

    plt.pie(
        df["TOTAL_REVENUE"],
        labels=df["PAYMENT_MODE"],
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title(chart_title)
    plt.savefig(chart_file, bbox_inches="tight")
    plt.close()

    return {
        "message": "Revenue by payment mode report generated",
        "payment_mode": payment_mode,
        "data": df.to_dict(orient="records"),
        "csv_file": csv_file,
        "piechart_file": chart_file
    }


# =====================================
# 3. VIEW REVENUE PIE CHART (opens as HTML page, no download)
# =====================================

@app.get("/download/revenue-piechart", response_class=FileResponse)
def download_revenue_piechart():
    chart_file = f"{REPORT_FOLDER}/revenue_by_payment_mode_piechart.png"

    if not os.path.exists(chart_file):
        raise HTTPException(
            status_code=404,
            detail="Revenue pie chart not found. Generate revenue report first."
        )

    return FileResponse(chart_file, media_type="image/png")

# =====================================
# 4. MOST USED PAYMENT METHOD
# =====================================

@app.get("/most-used-payment-method")
def most_used_payment_method():

    conn = get_connection()

    query = """
    SELECT PAYMENT_MODE,
           COUNT(*) AS TOTAL_TRANSACTIONS
    FROM ORDERS
    GROUP BY PAYMENT_MODE
    ORDER BY TOTAL_TRANSACTIONS DESC
    LIMIT 1
    """

    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No payment method data found"
        )

    csv_file = f"{REPORT_FOLDER}/most_used_payment_method.csv"
    df.to_csv(csv_file, index=False)

    return {
        "message": "Most used payment method report generated",
        "data": df.to_dict(orient="records"),
        "csv_file": csv_file
    }


# =====================================
# 5. PAYMENT METHOD USAGE ALL MODES
# This is for proper piechart, not LIMIT 1
# =====================================

@app.get("/payment-method-usage")
def payment_method_usage():

    conn = get_connection()

    query = """
    SELECT PAYMENT_MODE,
           COUNT(*) AS TOTAL_TRANSACTIONS
    FROM ORDERS
    GROUP BY PAYMENT_MODE
    ORDER BY TOTAL_TRANSACTIONS DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No payment usage data found"
        )

    csv_file = f"{REPORT_FOLDER}/payment_method_usage_all.csv"
    df.to_csv(csv_file, index=False)

    chart_file = f"{REPORT_FOLDER}/payment_method_usage_piechart.png"

    plt.figure(figsize=(8, 8))

    plt.pie(
        df["TOTAL_TRANSACTIONS"],
        labels=df["PAYMENT_MODE"],
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("Payment Method Usage")
    plt.savefig(chart_file, bbox_inches="tight")
    plt.close()

    return {
        "message": "Payment method usage report generated",
        "data": df.to_dict(orient="records"),
        "csv_file": csv_file,
        "piechart_file": chart_file
    }


# =====================================
# 6. VIEW PAYMENT METHOD USAGE PIE CHART (opens as HTML page, no download)
# =====================================

@app.get("/download/payment-method-usage-piechart", response_class=FileResponse)
def download_payment_method_usage_piechart():
    chart_file = f"{REPORT_FOLDER}/payment_method_usage_piechart.png"

    if not os.path.exists(chart_file):
        raise HTTPException(
            status_code=404,
            detail="Payment method usage pie chart not found. Generate report first."
        )

    return FileResponse(chart_file, media_type="image/png")



# =====================================
# 7. DIGITAL VS CASH
# =====================================

@app.get("/digital-vs-cash")
def digital_vs_cash():

    conn = get_connection()

    query = """
    SELECT
    CASE
    WHEN PAYMENT_MODE = 'Cash'
    THEN 'Cash'
    ELSE 'Digital'
    END AS TRANSACTION_TYPE,
    COUNT(*) AS TOTAL_TRANSACTIONS
    FROM ORDERS
    GROUP BY
    CASE
    WHEN PAYMENT_MODE = 'Cash'
    THEN 'Cash'
    ELSE 'Digital'
    END
    """

    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No digital vs cash data found"
        )

    csv_file = f"{REPORT_FOLDER}/digital_vs_cash.csv"
    df.to_csv(csv_file, index=False)

    chart_file = f"{REPORT_FOLDER}/digital_vs_cash_piechart.png"

    plt.figure(figsize=(8, 8))

    plt.pie(
        df["TOTAL_TRANSACTIONS"],
        labels=df["TRANSACTION_TYPE"],
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("Digital vs Cash Payments")
    plt.savefig(chart_file, bbox_inches="tight")
    plt.close()

    return {
        "message": "Digital vs Cash report generated",
        "data": df.to_dict(orient="records"),
        "csv_file": csv_file,
        "piechart_file": chart_file
    }


# =====================================
# 8. VIEW DIGITAL VS CASH PIE CHART (opens as HTML page, no download)
# =====================================

@app.get("/download/digital-vs-cash-piechart", response_class=FileResponse)
def download_digital_vs_cash_piechart():
    chart_file = f"{REPORT_FOLDER}/digital_vs_cash_piechart.png"

    if not os.path.exists(chart_file):
        raise HTTPException(
            status_code=404,
            detail="Digital vs Cash pie chart not found. Generate report first."
        )

    return FileResponse(chart_file, media_type="image/png")


# =====================================
# 9. HIGHEST REVENUE PRODUCT
# =====================================

@app.get("/highest-revenue-product")
def highest_revenue_product():

    conn = get_connection()

    query = """
    SELECT
        P.PRODUCT_ID,
        P.PRODUCT_NAME,
        SUM(OI.QUANTITY * P.UNIT_PRICE) AS TOTAL_REVENUE
    FROM ORDER_ITEMS OI
    JOIN PRODUCTS P
    ON OI.PRODUCT_ID = P.PRODUCT_ID
    GROUP BY
        P.PRODUCT_ID,
        P.PRODUCT_NAME
    ORDER BY TOTAL_REVENUE DESC
    LIMIT 1
    """

    try:
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="No highest revenue product data found"
            )

        csv_file = f"{REPORT_FOLDER}/highest_revenue_product.csv"
        df.to_csv(csv_file, index=False)

        return {
            "message": "Highest revenue product report generated",
            "data": df.to_dict(orient="records"),
            "csv_file": csv_file
        }

    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =====================================
# 10. GENERATE ALL REPORTS
# =====================================

@app.get("/generate-all-reports")
def generate_all_reports():

    generated_files = []

    # Revenue by all payment modes
    conn = get_connection()

    revenue_query = """
    SELECT PAYMENT_MODE,
           SUM(NET_AMOUNT) AS TOTAL_REVENUE
    FROM ORDERS
    WHERE ORDER_STATUS = 'Delivered'
    GROUP BY PAYMENT_MODE
    ORDER BY TOTAL_REVENUE DESC
    """

    revenue_df = pd.read_sql(revenue_query, conn)

    revenue_file = f"{REPORT_FOLDER}/revenue_by_payment_mode.csv"
    revenue_df.to_csv(revenue_file, index=False)
    generated_files.append(revenue_file)

    revenue_chart_file = f"{REPORT_FOLDER}/revenue_by_payment_mode_piechart.png"

    plt.figure(figsize=(8, 8))
    plt.pie(
        revenue_df["TOTAL_REVENUE"],
        labels=revenue_df["PAYMENT_MODE"],
        autopct="%1.1f%%",
        startangle=90
    )
    plt.title("Revenue By All Payment Modes")
    plt.savefig(revenue_chart_file, bbox_inches="tight")
    plt.close()
    generated_files.append(revenue_chart_file)

    # Most used payment method
    most_used_query = """
    SELECT PAYMENT_MODE,
           COUNT(*) AS TOTAL_TRANSACTIONS
    FROM ORDERS
    GROUP BY PAYMENT_MODE
    ORDER BY TOTAL_TRANSACTIONS DESC
    LIMIT 1
    """

    most_used_df = pd.read_sql(most_used_query, conn)

    most_used_file = f"{REPORT_FOLDER}/most_used_payment_method.csv"
    most_used_df.to_csv(most_used_file, index=False)
    generated_files.append(most_used_file)

    # Payment usage all modes
    usage_query = """
    SELECT PAYMENT_MODE,
           COUNT(*) AS TOTAL_TRANSACTIONS
    FROM ORDERS
    GROUP BY PAYMENT_MODE
    ORDER BY TOTAL_TRANSACTIONS DESC
    """

    usage_df = pd.read_sql(usage_query, conn)

    usage_file = f"{REPORT_FOLDER}/payment_method_usage_all.csv"
    usage_df.to_csv(usage_file, index=False)
    generated_files.append(usage_file)

    usage_chart_file = f"{REPORT_FOLDER}/payment_method_usage_piechart.png"

    plt.figure(figsize=(8, 8))
    plt.pie(
        usage_df["TOTAL_TRANSACTIONS"],
        labels=usage_df["PAYMENT_MODE"],
        autopct="%1.1f%%",
        startangle=90
    )
    plt.title("Payment Method Usage")
    plt.savefig(usage_chart_file, bbox_inches="tight")
    plt.close()
    generated_files.append(usage_chart_file)

    # Digital vs Cash
    digital_query = """
    SELECT
    CASE
    WHEN PAYMENT_MODE = 'Cash'
    THEN 'Cash'
    ELSE 'Digital'
    END AS TRANSACTION_TYPE,
    COUNT(*) AS TOTAL_TRANSACTIONS
    FROM ORDERS
    GROUP BY
    CASE
    WHEN PAYMENT_MODE = 'Cash'
    THEN 'Cash'
    ELSE 'Digital'
    END
    """

    digital_df = pd.read_sql(digital_query, conn)

    digital_file = f"{REPORT_FOLDER}/digital_vs_cash.csv"
    digital_df.to_csv(digital_file, index=False)
    generated_files.append(digital_file)

    digital_chart_file = f"{REPORT_FOLDER}/digital_vs_cash_piechart.png"

    plt.figure(figsize=(8, 8))
    plt.pie(
        digital_df["TOTAL_TRANSACTIONS"],
        labels=digital_df["TRANSACTION_TYPE"],
        autopct="%1.1f%%",
        startangle=90
    )
    plt.title("Digital vs Cash Payments")
    plt.savefig(digital_chart_file, bbox_inches="tight")
    plt.close()
    generated_files.append(digital_chart_file)

    # Highest revenue product
    highest_query = """
    SELECT
        P.PRODUCT_ID,
        P.PRODUCT_NAME,
        SUM(OI.QUANTITY * P.UNIT_PRICE) AS TOTAL_REVENUE
    FROM ORDER_ITEMS OI
    JOIN PRODUCTS P
    ON OI.PRODUCT_ID = P.PRODUCT_ID
    GROUP BY
        P.PRODUCT_ID,
        P.PRODUCT_NAME
    ORDER BY TOTAL_REVENUE DESC
    LIMIT 1
    """

    try:
        highest_df = pd.read_sql(highest_query, conn)

        highest_file = f"{REPORT_FOLDER}/highest_revenue_product.csv"
        highest_df.to_csv(highest_file, index=False)
        generated_files.append(highest_file)

    except Exception as e:
        generated_files.append(f"Highest revenue product skipped: {str(e)}")

    conn.close()

    return {
        "message": "All reports generated successfully",
        "generated_files": generated_files
    }