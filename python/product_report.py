from db_connection import get_connection
# writing the functionalities

def execute_query(query):
    connection = get_connection()

    if connection is None:
        return {"error": "Unable to connect to database"}

    try:
        cursor = connection.cursor()

        cursor.execute(query)

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        result = []

        for row in rows:
            result.append(dict(zip(columns, row)))

        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        connection.close()


def total_products():

    query = """
    SELECT COUNT(*) AS TOTAL_PRODUCTS
    FROM PRODUCTS;
    """

    return execute_query(query)


def products_by_category():

    query = """
    SELECT
        CATEGORY,
        COUNT(*) AS TOTAL_PRODUCTS
    FROM PRODUCTS
    GROUP BY CATEGORY
    ORDER BY TOTAL_PRODUCTS DESC;
    """

    return execute_query(query)


def top_selling_products():

    query = """
    SELECT
        P.PRODUCT_NAME,
        SUM(OI.QUANTITY) AS TOTAL_QUANTITY_SOLD
    FROM PRODUCTS P
    JOIN ORDER_ITEMS OI
        ON P.PRODUCT_ID = OI.PRODUCT_ID
    GROUP BY P.PRODUCT_NAME
    ORDER BY TOTAL_QUANTITY_SOLD DESC
    LIMIT 10;
    """

    return execute_query(query)


def highest_revenue_product():

    query = """
    SELECT
        P.PRODUCT_NAME,
        SUM(OI.QUANTITY * OI.UNIT_PRICE) AS TOTAL_REVENUE
    FROM PRODUCTS P
    JOIN ORDER_ITEMS OI
        ON P.PRODUCT_ID = OI.PRODUCT_ID
    GROUP BY P.PRODUCT_NAME
    ORDER BY TOTAL_REVENUE DESC
    LIMIT 1;
    """

    return execute_query(query)


def lowest_selling_product():

    query = """
    SELECT
        P.PRODUCT_NAME,
        SUM(OI.QUANTITY) AS TOTAL_QUANTITY_SOLD
    FROM PRODUCTS P
    JOIN ORDER_ITEMS OI
        ON P.PRODUCT_ID = OI.PRODUCT_ID
    GROUP BY P.PRODUCT_NAME
    ORDER BY TOTAL_QUANTITY_SOLD ASC
    LIMIT 1;
    """

    return execute_query(query)

def unsold_products():

    query = """
    SELECT
        P.PRODUCT_ID,
        P.PRODUCT_NAME,
        P.CATEGORY
    FROM PRODUCTS P
    LEFT JOIN ORDER_ITEMS OI
        ON P.PRODUCT_ID = OI.PRODUCT_ID
    WHERE OI.PRODUCT_ID IS NULL
    ORDER BY P.PRODUCT_NAME;
    """

    return execute_query(query)