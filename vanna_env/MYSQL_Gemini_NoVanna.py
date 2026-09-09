import mysql.connector
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
import dotenv

import os
dotenv.load_dotenv()

GEMINI_KEY=os.getenv("GEMINI_API_KEY")
MYPASSWORD=os.getenv("SQL_PASSWORD")
configure(api_key=GEMINI_KEY)
model=GenerativeModel(model_name="gemini-3.6-flash")

if MYPASSWORD is None:
    raise EnvironmentError("Mysql password is not set in environment variables..!!")
else:
    connect=mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password=MYPASSWORD,
        database="your_database",
        port=3306
    )

cursor=connect.cursor()

def get_database_schema():
    """Which returns the description of all the tables and columns in the DB"""
    cursor=connect.cursor()
    cursor.execute("SHOW TABLES")
    tables=[next(iter(row.values())) if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
    schema_text=""

    for table in tables:
        cursor.execute(f"DESCRIBE `{table}`")
        cols=cursor.fetchall()
        col_desc=", ".join(
            f"{col['Field']} {col['Type']}" if isinstance(col, dict) else f"{col[0]} {col[1]}"
            for col in cols
        )
        schema_text+=f"Table `{table}`: {col_desc}\n"

    return schema_text

def question_to_llm_for_sql(question,schema):
    """Which takes a natural language question and returns the SQL query using Gemini API"""

    prompt=f"""Your are an SQL generator.Given this schema:\n{schema}\n
Write only the SQL query to answer the following question:\n{question}\n
    """
    result=model.generate_content(prompt)
    sql_format=result.text.strip()
    sql_format= sql_format.replace("```sql", "").replace("```", "").strip()

    return sql_format

def execute_sql_query(conn,sql_query):
    cursor=conn.cursor()
    cursor.execute(sql_query)
    cols=[col[0] for col in cursor.description] if cursor.description is not None else []
    rows=cursor.fetchall()
    return cols,rows

def connect_answer_and_question(question):
    schema=get_database_schema()
    sql_query=question_to_llm_for_sql(question,schema)

    print(f"Generated Query is:\n{sql_query}\n")
    cols,rows=execute_sql_query(connect,sql_query)

    return cols,rows

question=input(str("Enter your question in simple english:"))

cols,rows=connect_answer_and_question(question)
print(cols,rows)

