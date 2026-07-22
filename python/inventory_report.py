import os
import uuid
import base64
from io import BytesIO

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles

from db_connection import get_connection


# --------------------------------------------------------------------------
# APP SETUP
# --------------------------------------------------------------------------

REPORTS_DIR = "../reports/inventory_reports"

os.makedirs(
    REPORTS_DIR,
    exist_ok=True
)


app = FastAPI(
    title="Retail Analytics API",
    version="1.0.0",
    description="""
    Retail Dashboard APIs.
    Every endpoint generates an HTML report containing
    table data and visualization.
    """
)


app.mount(
    "/reports",
    StaticFiles(directory=REPORTS_DIR),
    name="reports"
)


# --------------------------------------------------------------------------
# CHART GENERATION
# --------------------------------------------------------------------------

def df_to_base64_chart(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        kind: str = "bar"):


    if df.empty:
        return None


    fig, ax = plt.subplots(
        figsize=(10,5)
    )


    plot_df = df.head(30)


    if kind == "pie":

        ax.pie(
            plot_df[y_col],
            labels=plot_df[x_col],
            autopct="%1.1f%%"
        )

        ax.set_title(title)


    else:

        ax.bar(
            plot_df[x_col].astype(str),
            plot_df[y_col]
        )

        ax.set_title(title)

        ax.set_xlabel(x_col)

        ax.set_ylabel(y_col)

        plt.xticks(
            rotation=45,
            ha="right"
        )


    plt.tight_layout()


    buffer = BytesIO()


    fig.savefig(
        buffer,
        format="png",
        dpi=110
    )


    plt.close(fig)


    buffer.seek(0)


    return base64.b64encode(
        buffer.read()
    ).decode()



# --------------------------------------------------------------------------
# HTML REPORT
# --------------------------------------------------------------------------


def build_html_report(
        title,
        df,
        chart_base64):


    chart_html = ""


    if chart_base64:

        chart_html = f"""
        <img src="data:image/png;base64,{chart_base64}">
        """


    if df.empty:

        table_html = "<p>No data found</p>"

    else:

        table_html = df.to_html(
            index=False
        )



    return f"""
    <html>

    <head>

    <title>{title}</title>

    <style>

    body {{
        font-family: Arial;
        margin:40px;
    }}

    table {{
        border-collapse:collapse;
        width:100%;
    }}

    td,th {{
        border:1px solid black;
        padding:8px;
    }}

    img {{
        width:80%;
    }}

    </style>

    </head>


    <body>

    <h1>{title}</h1>

    {chart_html}

    {table_html}


    </body>

    </html>
    """



def save_report(
        title,
        df,
        x_col=None,
        y_col=None,
        kind="bar"):


    chart = None


    if x_col and y_col:

        chart = df_to_base64_chart(
            df,
            x_col,
            y_col,
            title,
            kind
        )


    html = build_html_report(
        title,
        df,
        chart
    )


    filename = (
        title.lower()
        .replace(" ","_")
        +"_"
        +uuid.uuid4().hex[:8]
        +".html"
    )


    filepath=os.path.join(
        REPORTS_DIR,
        filename
    )


    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)



    return "/reports/"+filename




def execute_query(
        query,
        request,
        title,
        x_col=None,
        y_col=None,
        kind="bar"):


    conn=get_connection()


    try:

        df=pd.read_sql(
            query,
            conn
        )


        report=save_report(
            title,
            df,
            x_col,
            y_col,
            kind
        )


        return {

            "count":len(df),

            "data":
                df.to_dict(
                    orient="records"
                ),

            "report_url":
                str(request.base_url)
                .rstrip("/")
                +
                report
        }


    finally:

        conn.close()



# ==========================================================================
# INVENTORY REPORTS
# ==========================================================================


# 1. Display all products

@app.get("/inventory/products")
def get_products(request:Request):


    query="""

    SELECT

        PRODUCT_ID,

        PRODUCT_NAME,
        CATEGORY

    FROM PRODUCTS

    ORDER BY PRODUCT_NAME;

    """


    return execute_query(
        query,
        request,
        "All Products"
    )




# 2. Display all categories


@app.get("/inventory/categories")
def get_categories(request:Request):


    query="""

    SELECT DISTINCT

        CATEGORY

    FROM PRODUCTS

    ORDER BY CATEGORY;

    """


    return execute_query(
        query,
        request,
        "All Categories"
    )





# 3. Quantity sold by product


@app.get("/inventory/quantity-sold-by-product")
def quantity_sold(
        request:Request,
        product_name:str=Query(...)
):


    query="""

    SELECT

        P.PRODUCT_NAME,

        SUM(OI.QUANTITY) AS TOTAL_SOLD


    FROM ORDER_ITEMS OI


    JOIN PRODUCTS P

    ON OI.PRODUCT_ID=P.PRODUCT_ID


    WHERE UPPER(P.PRODUCT_NAME)
          =
          UPPER(%s)


    GROUP BY P.PRODUCT_NAME

    """


    conn=get_connection()


    try:


        df=pd.read_sql(
            query,
            conn,
            params=[product_name]
        )


        report=save_report(
            "Quantity Sold By Product",
            df,
            "PRODUCT_NAME",
            "TOTAL_SOLD"
        )


        return {

            "product_name":product_name,

            "data":
                df.to_dict(
                    orient="records"
                ),

            "report_url":
                str(request.base_url)
                .rstrip("/")
                +
                report
        }


    finally:

        conn.close()




# 4. Category wise sales with pie chart


@app.get("/inventory/category-wise-sales")
def category_sales(
    request: Request,
    category_name: str = Query(
        None,
        description="Enter category name (optional). Leave empty for all categories."
    )
):

    if category_name:

        # Specific category sales
        query = """
        SELECT
            P.CATEGORY,
            SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
            ON OI.PRODUCT_ID = P.PRODUCT_ID
        WHERE UPPER(P.CATEGORY)=UPPER(%s)
        GROUP BY P.CATEGORY;
        """

        conn = get_connection()

        try:

            df = pd.read_sql(
                query,
                conn,
                params=[category_name]
            )


            report_path = save_report(
                f"{category_name} Sales",
                df,
                x_col="CATEGORY",
                y_col="TOTAL_SOLD",
                kind="pie"
            )


            return {
                "type": "single category sales",
                "category": category_name,
                "count": len(df),
                "data": df.to_dict(
                    orient="records"
                ),
                "report_url":
                    str(request.base_url)
                    .rstrip("/")
                    +
                    report_path
            }


        finally:
            conn.close()


    else:

        # All category sales
        query = """
        SELECT
            P.CATEGORY,
            SUM(OI.QUANTITY) AS TOTAL_SOLD
        FROM ORDER_ITEMS OI
        JOIN PRODUCTS P
            ON OI.PRODUCT_ID = P.PRODUCT_ID
        GROUP BY P.CATEGORY
        ORDER BY TOTAL_SOLD DESC;
        """


        return execute_query(
            query,
            request,
            "Category Wise Sales",
            x_col="CATEGORY",
            y_col="TOTAL_SOLD",
            kind="pie"
        )


# 5. Top products with category


@app.get("/inventory/top-products")
def top_products(
        request:Request,
        top_n:int=Query(
            10,
            ge=1,
            le=100
        )
):


    query=f"""

    SELECT

        P.PRODUCT_NAME,

        P.CATEGORY,

        SUM(OI.QUANTITY) AS TOTAL_SOLD


    FROM ORDER_ITEMS OI


    JOIN PRODUCTS P

    ON OI.PRODUCT_ID=P.PRODUCT_ID


    GROUP BY

        P.PRODUCT_NAME,

        P.CATEGORY


    ORDER BY TOTAL_SOLD DESC


    LIMIT {top_n};

    """


    return execute_query(

        query,

        request,

        f"Top {top_n} Products",

        "PRODUCT_NAME",

        "TOTAL_SOLD"

    )