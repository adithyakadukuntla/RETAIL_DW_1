import os 
import snowflake.connector as sc
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    connection = sc.connect( 
        user=os.getenv("user"), 
        password=os.getenv("password"), 
        account=os.getenv("account"), 
        warehouse="COMPUTE_WH", 
        database="INVESCO_TRAINING", 
        schema="EMPLOYEE_DATA" 
    ) 
    print("Connected Successfully! ✅") 
    return connection