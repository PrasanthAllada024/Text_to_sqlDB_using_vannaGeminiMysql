import os
from dotenv import load_dotenv
load_dotenv()  

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from google.generativeai.client import configure
from vanna.legacy.google.gemini_chat import GoogleGeminiChat
from vanna.legacy.chromadb.chromadb_vector import ChromaDB_VectorStore

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY is None:
    raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")


os.environ["GOOGLE_API_KEY"] = GEMINI_KEY
configure(api_key=GEMINI_KEY)

class SqlVanna(ChromaDB_VectorStore,GoogleGeminiChat):
    def __init__(self,config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        GoogleGeminiChat.__init__(self, config={
            'api_key': GEMINI_KEY,
            'model_name': 'gemini-3.6-flash'
        })

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chroma_data")
CHROMA_PATH = os.path.abspath(CHROMA_PATH)
print(f"Using Chroma path: {CHROMA_PATH}")

vn = SqlVanna(config={'path': CHROMA_PATH})
sql_password=os.getenv("MYSQL_PASSWORD")
if sql_password is None:
    raise EnvironmentError("MYSQL_PASSWORD environment variable is not set.")
try:
    vn.connect_to_mysql(
        host='127.0.0.1',
        user='root',
        dbname='your_database',
        password=sql_password,
        port=3306
    )
    print("Database connection is successful...!!")
except Exception as e:
    print(f"Database connection failed: {e}")
    raise

try:
    tables_info = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'your_database'")
    print(f"Fetched {len(tables_info)} columns from INFORMATION_SCHEMA")
    print(tables_info.head().to_string())
    plan = vn.get_training_plan_generic(tables_info)
    print("Training plan created, training...")
    vn.train(plan=plan)
    print("Training complete.")
except Exception as e:
    print(f"Training failed: {e}")
    import traceback; traceback.print_exc()

try:
    query=input(str("Enter your SQL query in simple English: "))
    result = vn.ask(query)
    print("Final_results:")
    print(result)
except Exception as e:
    print(f"Ask failed: {e}")
    import traceback; traceback.print_exc()
