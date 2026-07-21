from fastapi import FastAPI
from inventory_report import router

app = FastAPI()

app.include_router(router)

@app.get("/")
def home():
    return {
        "message": "Retail Data Warehouse API is running successfully!"
    }