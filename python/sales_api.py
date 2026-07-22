
import os
import uuid
import base64
from io import BytesIO
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from db_connection import get_connection

app = FastAPI(
    title="Retail Analytics API",
    version="1.0.0",
)


BASE_DIR = os.path.dirname(os.path.abspath("C:/Users/Administrator/Retail_dw"))

REPORTS_DIR = os.path.join(BASE_DIR, "reports/sales")
CSV_DIR = os.path.join(BASE_DIR, "csv/sales")
CHART_DIR = os.path.join(BASE_DIR, "charts/sales")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")
app.mount("/csv", StaticFiles(directory=CSV_DIR), name="csv")
app.mount("/charts", StaticFiles(directory=CHART_DIR), name="charts")

def execute_query(query, params=None):

    conn = None
    cursor = None

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(query, params if params else ())

        columns = [i[0] for i in cursor.description]

        rows = cursor.fetchall()

        return pd.DataFrame(rows, columns=columns)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

def dataframe_chart(df, x_col, y_col, title, chart_type="bar"):

    if df.empty:
        return None

    plt.figure(figsize=(10,5))

    if chart_type == "bar":

        plt.bar(df[x_col].astype(str), df[y_col])

    elif chart_type == "line":

        plt.plot(
            df[x_col].astype(str),
            df[y_col],
            marker="o",
            linewidth=2
        )

    elif chart_type == "pie":

        plt.pie(
            df[y_col],
            labels=df[x_col].astype(str),
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops=dict(
                width=0.45,
                edgecolor="white"
            )
        )

        plt.axis("equal")

        plt.title(title)

    if chart_type != "pie":

        plt.xticks(rotation=45)

        xlabel = "Year" if title == "Custom Month Sales Report" else x_col

        plt.xlabel(xlabel)
        plt.ylabel(y_col)

    plt.tight_layout()

    buffer = BytesIO()

    plt.savefig(buffer, format="png")

    plt.close()

    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode()

def build_html_report(title, df, chart=None):

    chart_html = ""

    if chart:

        chart_html = f"""
        <div style="text-align:center">
            <img
                src="data:image/png;base64,{chart}"
                width="900">
        </div>
        """

    if df.empty:

        table = "<h3>No Records Found</h3>"

    else:

        table = df.to_html(
            index=False,
            classes="table"
        )

    return f"""
<!DOCTYPE html>

<html>

<head>

<title>{title}</title>

<style>

body{{
font-family:Arial;
background:#F5F5F5;
margin:40px;
}}

.card{{
background:white;
padding:30px;
border-radius:10px;
box-shadow:0 0 10px gray;
}}

h1{{
color:#1E88E5;
}}

.table{{
width:100%;
border-collapse:collapse;
}}

.table th{{
background:#1E88E5;
color:white;
padding:10px;
}}

.table td{{
padding:10px;
border:1px solid #ddd;
}}

.footer{{
margin-top:30px;
font-size:14px;
color:gray;
}}

</style>

</head>

<body>

<div class="card">

<h1>{title}</h1>

<p>

Generated :
{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

</p>

{chart_html}

{table}

<div class="footer">

Retail Analytics API

</div>

</div>

</body>

</html>

"""


def save_report(
        title,
        df,
        chart_type=None,
        x_col=None,
        y_col=None
):

    report_id = uuid.uuid4().hex[:8]

    csv_name = f"{title.lower().replace(' ','_')}_{report_id}.csv"

    html_name = f"{title.lower().replace(' ','_')}_{report_id}.html"

    csv_path = os.path.join(CSV_DIR, csv_name)

    df.to_csv(csv_path, index=False)

    chart = None

    if chart_type:

        chart = dataframe_chart(
            df,
            x_col,
            y_col,
            title,
            chart_type
        )

    html = build_html_report(
        title,
        df,
        chart
    )

    html_path = os.path.join(REPORTS_DIR, html_name)

    with open(html_path, "w", encoding="utf8") as f:

        f.write(html)

    return {
        "status": "success",
        "report_url": f"http://127.0.0.1:8000/reports/{html_name}",
        "csv_url": f"http://127.0.0.1:8000/csv/{csv_name}"
    }


def append_date_filter(query, params, start_date, end_date):

    if start_date and end_date:

        query += " AND TO_DATE(o.ORDER_DATE) BETWEEN %s AND %s"

        params.extend([
            start_date,
            end_date
        ])

    return query

@app.get("/total-orders")
def total_orders(
    start_date: str = None,
    end_date: str = None
):

    query = """
    SELECT
        COUNT(*) AS TOTAL_ORDERS
    FROM ORDERS o
    WHERE 1=1
    """

    params = []

    query = append_date_filter(
        query,
        params,
        start_date,
        end_date
    )

    df = execute_query(
        query,
        tuple(params)
    )

    return save_report(
        "Total Orders",
        df
    )


@app.get("/total-revenue")
def total_revenue(
    start_date: str = None,
    end_date: str = None
):

    query = """
    SELECT
        ROUND(SUM(NET_AMOUNT),2)
        AS TOTAL_REVENUE
    FROM ORDERS o
    WHERE 1=1
    """

    params = []

    query = append_date_filter(
        query,
        params,
        start_date,
        end_date
    )

    df = execute_query(
        query,
        tuple(params)
    )

    return save_report(
        "Total Revenue",
        df
    )


@app.get("/average-order-value")
def average_order_value(
    start_date: str = None,
    end_date: str = None
):

    query = """
    SELECT
        ROUND(
            AVG(NET_AMOUNT),
            2
        ) AS AVG_ORDER_VALUE
    FROM ORDERS o
    WHERE 1=1
    """

    params = []

    query = append_date_filter(
        query,
        params,
        start_date,
        end_date
    )

    df = execute_query(
        query,
        tuple(params)
    )

    return save_report(
        "Average Order Value",
        df
    )


@app.get("/dashboard-summary")
def dashboard_summary():

    orders = execute_query("""
    SELECT COUNT(*) TOTAL_ORDERS
    FROM ORDERS
    """)

    revenue = execute_query("""
    SELECT ROUND(SUM(NET_AMOUNT),2)
    TOTAL_REVENUE
    FROM ORDERS
    """)

    avg = execute_query("""
    SELECT ROUND(
        AVG(NET_AMOUNT),2
    ) AVG_ORDER_VALUE
    FROM ORDERS
    """)

    dashboard = pd.DataFrame({

        "Metric":[
            "Total Orders",
            "Total Revenue",
            "Average Order Value"
        ],

        "Value":[
            orders.iloc[0,0],
            revenue.iloc[0,0],
            avg.iloc[0,0]
        ]

    })

    return save_report(
        "Dashboard Summary",
        dashboard
    )


@app.get("/monthly-sales")
def monthly_sales(
    year: int = None,
    month: int = None
):

    query = """
    SELECT

        YEAR(TO_DATE(o.ORDER_DATE)) AS SALES_YEAR,

        MONTH(TO_DATE(o.ORDER_DATE)) AS SALES_MONTH,

        ROUND(SUM(o.NET_AMOUNT),2) AS SALES

    FROM ORDERS o

    WHERE 1=1
    """

    params = []

    if year is not None:

        query += """
        AND YEAR(TO_DATE(o.ORDER_DATE))=%s
        """

        params.append(year)

    if month is not None:

        query += """
        AND MONTH(TO_DATE(o.ORDER_DATE))=%s
        """

        params.append(month)

    query += """

    GROUP BY

        SALES_YEAR,
        SALES_MONTH

    ORDER BY

        SALES_YEAR,
        SALES_MONTH

    """

    df = execute_query(
        query,
        tuple(params)
    )

    if not df.empty:

        df["PERIOD"] = (

            df["SALES_YEAR"].astype(str)

            + "-"

            + df["SALES_MONTH"].astype(str).str.zfill(2)

        )

        report_df = df[["PERIOD", "SALES"]]

    else:

        report_df = pd.DataFrame(
            columns=["PERIOD", "SALES"]
        )

    return save_report(

        title="Monthly Sales",

        df=report_df,

        chart_type="line",

        x_col="PERIOD",

        y_col="SALES"

    )


@app.get("/state-sales")
def state_sales(

    start_date: str = None,

    end_date: str = None,

    state: str = None

):

    query = """

    SELECT

        s.STATE,

        ROUND(
            SUM(o.NET_AMOUNT),
            2
        ) AS SALES

    FROM ORDERS o

    JOIN STORES s

    ON o.STORE_ID=s.STORE_ID

    WHERE 1=1

    """

    params = []

    query = append_date_filter(

        query,

        params,

        start_date,

        end_date

    )

    if state:

        query += """

        AND s.STATE=%s

        """

        params.append(state)

    query += """

    GROUP BY

        s.STATE

    ORDER BY

        SALES DESC

    """

    df = execute_query(

        query,

        tuple(params)

    )

    return save_report(

        title="State Wise Sales",

        df=df,

        chart_type="pie",

        x_col="STATE",

        y_col="SALES"

    )


@app.get("/city-sales")
def city_sales(

    start_date: str = None,

    end_date: str = None,

    city: str = None

):

    query = """

    SELECT

        s.CITY,

        ROUND(
            SUM(o.NET_AMOUNT),
            2
        ) AS SALES

    FROM ORDERS o

    JOIN STORES s

    ON o.STORE_ID=s.STORE_ID

    WHERE 1=1

    """

    params = []

    query = append_date_filter(

        query,

        params,

        start_date,

        end_date

    )

    if city:

        query += """

        AND s.CITY=%s

        """

        params.append(city)

    query += """

    GROUP BY

        s.CITY

    ORDER BY

        SALES DESC

    """

    df = execute_query(

        query,

        tuple(params)

    )

    return save_report(

        title="City Wise Sales",

        df=df,

        chart_type="pie",

        x_col="CITY",

        y_col="SALES"

    )


@app.get("/store-sales")
def store_sales(

    start_date: str = None,

    end_date: str = None,

    store: str = None

):

    query = """

    SELECT

        s.STORE_NAME,

        ROUND(
            SUM(o.NET_AMOUNT),
            2
        ) AS SALES

    FROM ORDERS o

    JOIN STORES s

        ON o.STORE_ID = s.STORE_ID

    WHERE 1=1

    """

    params = []

    query = append_date_filter(

        query,

        params,

        start_date,

        end_date

    )

    if store:

        query += """

        AND s.STORE_NAME=%s

        """

        params.append(store)

    query += """

    GROUP BY

        s.STORE_NAME

    ORDER BY

        SALES DESC

    """

    df = execute_query(

        query,

        tuple(params)

    )

    return save_report(

        title="Store Wise Sales",

        df=df,

        chart_type="bar",

        x_col="STORE_NAME",

        y_col="SALES"

    )


@app.get("/category-sales")
def category_sales(

    start_date: str = None,

    end_date: str = None,

    category: str = None

):

    query = """

    SELECT

        p.CATEGORY,

        ROUND(

            SUM(oi.LINE_TOTAL),

            2

        ) AS SALES

    FROM ORDER_ITEMS oi

    JOIN PRODUCTS p

        ON oi.PRODUCT_ID=p.PRODUCT_ID

    JOIN ORDERS o

        ON oi.ORDER_ID=o.ORDER_ID

    WHERE 1=1

    """

    params = []

    if start_date and end_date:

        query += """

        AND TO_DATE(o.ORDER_DATE)

        BETWEEN %s AND %s

        """

        params.extend([

            start_date,

            end_date

        ])

    if category:

        query += """

        AND p.CATEGORY=%s

        """

        params.append(category)

    query += """

    GROUP BY

        p.CATEGORY

    ORDER BY

        SALES DESC

    """

    df = execute_query(

        query,

        tuple(params)

    )

    return save_report(

        title="Category Wise Sales",

        df=df,

        chart_type="pie",

        x_col="CATEGORY",

        y_col="SALES"

    )



@app.get("/top-products")
def top_products(

    start_date: str = None,

    end_date: str = None

):

    query = """

    SELECT

        p.PRODUCT_NAME,

        ROUND(

            SUM(oi.LINE_TOTAL),

            2

        ) AS SALES

    FROM ORDER_ITEMS oi

    JOIN PRODUCTS p

        ON oi.PRODUCT_ID=p.PRODUCT_ID

    JOIN ORDERS o

        ON oi.ORDER_ID=o.ORDER_ID

    WHERE 1=1

    """

    params = []

    if start_date and end_date:

        query += """

        AND TO_DATE(o.ORDER_DATE)

        BETWEEN %s AND %s

        """

        params.extend([

            start_date,

            end_date

        ])

    query += """

    GROUP BY

        p.PRODUCT_NAME

    ORDER BY

        SALES DESC

    LIMIT 10

    """

    df = execute_query(

        query,

        tuple(params)

    )

    return save_report(

        title="Top 10 Products",

        df=df,

        chart_type="bar",

        x_col="PRODUCT_NAME",

        y_col="SALES"

    )


@app.get("/top-stores")
def top_stores(

    start_date: str = None,

    end_date: str = None

):

    query = """

    SELECT

        s.STORE_NAME,

        ROUND(

            SUM(o.NET_AMOUNT),

            2

        ) AS SALES

    FROM ORDERS o

    JOIN STORES s

        ON o.STORE_ID=s.STORE_ID

    WHERE 1=1

    """

    params = []

    query = append_date_filter(

        query,

        params,

        start_date,

        end_date

    )

    query += """

    GROUP BY

        s.STORE_NAME

    ORDER BY

        SALES DESC

    LIMIT 10

    """

    df = execute_query(

        query,

        tuple(params)

    )

    return save_report(

        title="Top 10 Stores",

        df=df,

        chart_type="bar",

        x_col="STORE_NAME",

        y_col="SALES"

    )


from fastapi.responses import HTMLResponse


@app.get("/customizable-sales", response_class=HTMLResponse)
def customizable_sales_page():

    return """

<!DOCTYPE html>

<html>

<head>

<title>
Retail Custom Sales Dashboard
</title>


<style>


body{

    font-family: Arial, sans-serif;

    background:#f4f6f9;

    margin:40px;

}



.container{

    width:900px;

    margin:auto;

    background:white;

    padding:35px;

    border-radius:12px;

    box-shadow:0px 0px 15px #ccc;

}



h1{

    text-align:center;

    color:#1565c0;

}



.row{

    display:flex;

    gap:20px;

    margin-top:20px;

}



.col{

    flex:1;

}



label{

    font-weight:bold;

    display:block;

    margin-bottom:8px;

}



input,select{

    width:100%;

    padding:10px;

    border-radius:5px;

    border:1px solid #aaa;

}



button{

    margin-top:35px;

    width:100%;

    padding:15px;

    background:#1565c0;

    color:white;

    border:none;

    border-radius:8px;

    font-size:18px;

    cursor:pointer;

}



button:hover{

    background:#0d47a1;

}



</style>

</head>


<body>


<div class="container">


<h1>
Custom Sales Report
</h1>



<div class="row">


<div class="col">

<label>
Start Date
</label>

<input 
type="date"
id="start_date">

</div>



<div class="col">

<label>
End Date
</label>

<input 
type="date"
id="end_date">

</div>


</div>





<div class="row">


<div class="col">

<label>
State
</label>


<select id="state">

<option value="">
All States
</option>

</select>


</div>



<div class="col">


<label>
City
</label>


<select id="city">

<option value="">
All Cities
</option>


</select>


</div>


</div>






<div class="row">


<div class="col">


<label>
Store
</label>


<select id="store">

<option value="">
All Stores
</option>


</select>


</div>




<div class="col">


<label>
Category
</label>


<select id="category">


<option value="">
All Categories
</option>


</select>



</div>


</div>


<div class="row">


<div class="col">


<label>
Report Type
</label>



<select id="report_type">


<option value="month">
Monthly Sales
</option>


<option value="state">
State Wise Sales
</option>


<option value="city">
City Wise Sales
</option>


<option value="store">
Store Wise Sales
</option>


<option value="category">
Category Wise Sales
</option>


</select>


</div>


</div>






<button onclick="generateReport()">

Generate Report

</button>

</div>

<script>



fetch("/states")

.then(response=>response.json())

.then(data=>{


let state=document.getElementById("state");


data.forEach(item=>{


state.innerHTML +=

`
<option value="${item}">
${item}
</option>

`;


});


});





// =====================================================
// LOAD CATEGORIES
// =====================================================


fetch("/categories")

.then(response=>response.json())

.then(data=>{


let category=document.getElementById("category");


data.forEach(item=>{


category.innerHTML +=

`
<option value="${item}">
${item}
</option>

`;


});


});







// =====================================================
// STATE CHANGE -> CITY LOAD
// =====================================================



document
.getElementById("state")
.onchange=function(){


let state=this.value;



fetch(

"/cities?state="+

encodeURIComponent(state)

)



.then(response=>response.json())


.then(data=>{


let city=document
.getElementById("city");



city.innerHTML=

`
<option value="">
All Cities
</option>
`;



data.forEach(item=>{


city.innerHTML +=

`
<option value="${item}">
${item}
</option>

`;


});



});


};







// =====================================================
// CITY CHANGE -> STORE LOAD
// =====================================================



document
.getElementById("city")
.onchange=function(){



let city=this.value;


let state=document
.getElementById("state")
.value;




fetch(

"/stores?state="+

encodeURIComponent(state)

+

"&city="+

encodeURIComponent(city)

)




.then(response=>response.json())


.then(data=>{


let store=document
.getElementById("store");



store.innerHTML=

`
<option value="">
All Stores
</option>
`;



data.forEach(item=>{


store.innerHTML +=

`
<option value="${item}">
${item}
</option>

`;


});


});



};








// =====================================================
// GENERATE REPORT
// =====================================================



function generateReport(){



let url="/generate-report?";



url +=

"group_by="

+

document
.getElementById("report_type")
.value;



url +=

"&start_date="

+

document
.getElementById("start_date")
.value;



url +=

"&end_date="

+

document
.getElementById("end_date")
.value;



url +=

"&state="

+

encodeURIComponent(

document
.getElementById("state")
.value

);



url +=

"&city="

+

encodeURIComponent(

document
.getElementById("city")
.value

);



url +=

"&store="

+

encodeURIComponent(

document
.getElementById("store")
.value

);



url +=

"&category="

+

encodeURIComponent(

document
.getElementById("category")
.value

);





fetch(url)


.then(response=>response.json())


.then(data=>{


window.location.href=

data.report_url;


})



.catch(error=>{


alert(
"Error generating report"
);


console.log(error);



});



}




</script>


</body>

</html>

"""
# ==========================================================
# STATE DROPDOWN
# ==========================================================

@app.get("/states")
def get_states():

    query = """
    SELECT DISTINCT STATE
    FROM STATE_CITY_MAP
    ORDER BY STATE
    """

    df = execute_query(query)

    return df["STATE"].tolist()



# ==========================================================
# CITY DROPDOWN
# ==========================================================

@app.get("/cities")
def get_cities(
    state:str=None
):

    query = """
    SELECT DISTINCT CITY
    FROM STATE_CITY_MAP
    WHERE 1=1
    """

    params=[]


    if state:

        query += """
        AND STATE=%s
        """

        params.append(state)



    query += """
    ORDER BY CITY
    """

    df = execute_query(
        query,
        tuple(params)
    )


    return df["CITY"].tolist()



@app.get("/stores")
def get_stores(
    state:str=None,
    city:str=None
):

    query="""

    SELECT DISTINCT

        STORE_NAME

    FROM STORES

    WHERE 1=1

    """

    params=[]


    if state:

        query += """
        AND STATE=%s
        """

        params.append(state)



    if city:

        query += """
        AND CITY=%s
        """

        params.append(city)



    query += """
    ORDER BY STORE_NAME
    """

    df=execute_query(
        query,
        tuple(params)
    )


    return df["STORE_NAME"].tolist()
# ==========================================================
# GENERATE CUSTOM SALES REPORT
# ==========================================================


@app.get("/generate-report")
def generate_report(

    group_by:str,

    start_date:str=None,

    end_date:str=None,

    state:str=None,

    city:str=None,

    store:str=None,

    category:str=None

):


    group_by = group_by.lower()



    # ------------------------------------------------------
    # SELECT COLUMN AND CHART TYPE
    # ------------------------------------------------------


    if group_by == "month":


        select_column = """

        CONCAT(

        YEAR(TO_DATE(o.ORDER_DATE)),

        '-',

        LPAD(
        MONTH(TO_DATE(o.ORDER_DATE)),
        2,
        '0'
        )

        )

        AS LABEL

        """


        group_column = """

        YEAR(TO_DATE(o.ORDER_DATE)),

        MONTH(TO_DATE(o.ORDER_DATE))

        """


        chart_type="line"



    elif group_by == "state":


        select_column = """

        s.STATE AS LABEL

        """


        group_column = """

        s.STATE

        """


        chart_type="pie"




    elif group_by == "city":


        select_column = """

        s.CITY AS LABEL

        """


        group_column = """

        s.CITY

        """


        chart_type="pie"




    elif group_by == "store":


        select_column = """

        s.STORE_NAME AS LABEL

        """


        group_column = """

        s.STORE_NAME

        """


        chart_type="bar"





    elif group_by == "category":


        select_column = """

        p.CATEGORY AS LABEL

        """


        group_column = """

        p.CATEGORY

        """


        chart_type="pie"




    else:


        raise HTTPException(

            status_code=400,

            detail="Invalid report type"

        )




    # ------------------------------------------------------
    # BASE QUERY
    # ------------------------------------------------------


    query=f"""

    SELECT


    {select_column},


    ROUND(

        SUM(oi.LINE_TOTAL),

        2

    ) AS SALES



    FROM ORDERS o



    JOIN ORDER_ITEMS oi

    ON o.ORDER_ID = oi.ORDER_ID



    JOIN PRODUCTS p

    ON oi.PRODUCT_ID = p.PRODUCT_ID



    JOIN STORES s

    ON o.STORE_ID = s.STORE_ID



    WHERE 1=1



    """



    params=[]





    # ------------------------------------------------------
    # DATE FILTER
    # ------------------------------------------------------


    if start_date and end_date:


        query += """

        AND TO_DATE(o.ORDER_DATE)

        BETWEEN %s AND %s

        """


        params.extend([

            start_date,

            end_date

        ])





    # ------------------------------------------------------
    # STATE FILTER
    # ------------------------------------------------------


    if state:


        query += """

        AND s.STATE=%s

        """


        params.append(state)






    # ------------------------------------------------------
    # CITY FILTER
    # ------------------------------------------------------


    if city:


        query += """

        AND s.CITY=%s

        """


        params.append(city)







    # ------------------------------------------------------
    # STORE FILTER
    # ------------------------------------------------------


    if store:


        query += """

        AND s.STORE_NAME=%s

        """


        params.append(store)







    # ------------------------------------------------------
    # CATEGORY FILTER
    # ------------------------------------------------------


    if category:


        query += """

        AND p.CATEGORY=%s

        """


        params.append(category)







    # ------------------------------------------------------
    # GROUP BY
    # ------------------------------------------------------

    if group_by == "month":

        query += f"""

        GROUP BY

        {group_column}


        ORDER BY

        YEAR(TO_DATE(o.ORDER_DATE)),

        MONTH(TO_DATE(o.ORDER_DATE))

        """

    else:

        query += f"""

    GROUP BY

    {group_column}


    ORDER BY

    SALES DESC

    """




    print("==============================")

    print(query)

    print(params)

    print("==============================")





    df = execute_query(
        query,
        tuple(params)
    )

    if group_by == "month" and not df.empty:

        df = df.sort_values(by="LABEL")

        # Rename column for report table
        df.rename(
            columns={"LABEL": "YEAR"},
            inplace=True
        )




    # ------------------------------------------------------
    # GENERATE REPORT
    # ------------------------------------------------------


    report = save_report(

        title=f"Custom {group_by.title()} Sales Report",

        df=df,

        chart_type=chart_type,

        x_col="YEAR" if group_by == "month" else "LABEL",

        y_col="SALES"

    )




    report["filters"]={


        "start_date":start_date,


        "end_date":end_date,


        "state":state,


        "city":city,


        "store":store,


        "category":category,


        "group_by":group_by


    }



    return report