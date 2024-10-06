import pandas as pd
from sqlalchemy import create_engine
from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator

# Database connection configurations
DATABASE_TYPE = 'postgresql'
DBAPI = 'psycopg2'
USER = 'user'
PASSWORD = 'password'
HOST = 'localhost'
PORT_TR = '5433'
DATABASE_TR = 'transactional_db'

# Create a database URI for the transactional database
db_uri_tr = f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{HOST}:{PORT_TR}/{DATABASE_TR}"
engine_tr = create_engine(db_uri_tr)

PORT_DWH = '5434'
DATABASE_DWH = 'dwh_db'

# Create a database URI for the data warehouse
db_uri_dwh = f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{HOST}:{PORT_DWH}/{DATABASE_DWH}"
engine_dwh = create_engine(db_uri_dwh)

# Define the DAG
with DAG("ETL_DAG", start_date=datetime(2021, 1, 1), schedule_interval="@daily", catchup=False) as dag:
    
    def extract(**kwargs):
        # Extract data from the transactional database
        queries = {
            "users": "SELECT * FROM users;",
            "authors": "SELECT * FROM authors;",
            "books": "SELECT * FROM books;",
            "reviews": "SELECT * FROM reviews;",
            "orders": "SELECT * FROM orders;",
            "order_book": "SELECT * FROM order_book;"
        }

        dataframes = {name: pd.read_sql(query, engine_tr) for name, query in queries.items()}
        return dataframes

    def transform(**kwargs):
        # Transform the data (implement your transformation logic here)
        dataframes = kwargs['task_instance'].xcom_pull(task_ids='extract_phase')
        return dataframes  # Placeholder for transformation logic

    def load(**kwargs):
        # Load the data into the data warehouse
        dataframes = kwargs['task_instance'].xcom_pull(task_ids='transform_phase')
        for name, df in dataframes.items():
            df.to_sql(name, engine_dwh, if_exists="replace", index=False)
    
    # Define tasks
    extract_phase = PythonOperator(
        task_id="extract_phase",
        python_callable=extract,
        provide_context=True,
    )

    transform_phase = PythonOperator(
        task_id="transform_phase",
        python_callable=transform,
        provide_context=True,
    )

    load_phase = PythonOperator(
        task_id="load_phase",
        python_callable=load,
        provide_context=True,
    )

    email_status = EmailOperator(
        task_id='email_on_success',
        to='Kariemg05@gmail.com',
        subject='Pipeline Success',
        html_content='The pipeline has completed successfully.',
    )

    # Set task dependencies
    extract_phase >> transform_phase >> load_phase >> email_status
