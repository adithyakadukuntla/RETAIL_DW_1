from fastapi import FastAPI

from product_report import (
    total_products,
    products_by_category,
    top_selling_products,
    highest_revenue_product,
    lowest_selling_product,
    unsold_products
)

app = FastAPI(
    title="Retail Data Warehouse API",
    description="Product Reports API",
    version="1.0"
)


@app.get("/")
def home():
    return {"message": "Retail Data Warehouse API is running."}


@app.get("/products/total")
def get_total_products():
    return total_products()


@app.get("/products/category")
def get_products_by_category():
    return products_by_category()


@app.get("/products/top-selling")
def get_top_selling_products():
    return top_selling_products()


@app.get("/products/highest-revenue")
def get_highest_revenue_product():
    return highest_revenue_product()


@app.get("/products/lowest-selling")
def get_lowest_selling_product():
    return lowest_selling_product()

@app.get("/products/unsold")
def get_unsold_products():
    return unsold_products()