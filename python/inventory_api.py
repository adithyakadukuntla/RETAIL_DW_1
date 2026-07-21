from fastapi import APIRouter
import pandas as pd
import os
from db_connection import get_connection

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory Reports"]
)

os.makedirs("output", exist_ok=True)