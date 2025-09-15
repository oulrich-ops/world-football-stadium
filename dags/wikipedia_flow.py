from airflow.sdk import DAG, task
from datetime import datetime
from airflow.providers.standard.operators.bash import BashOperator
import sys

sys.path.append("/opt/airflow/pipelines")
from data_extraction import (
    get_data_from_wikipedia,
    extract_data_from_text,
    transform_data,
    load_data,
)


with DAG(
    dag_id="wikipedia_flow",
    start_date=datetime(2022, 1, 1),
    schedule="0 0 * * *",
    catchup=False,
    tags=["football", "wikipedia"],
) as dag:

    @task()
    def extraction_task():
        text = get_data_from_wikipedia(
            "https://en.wikipedia.org/wiki/List_of_association_football_stadiums_by_capacity"
        )
        return extract_data_from_text(text)

    @task()
    def data_trasnformation_task(data):
        return transform_data(data)

    @task()
    def data_loading_task(data):
        load_data(data)

    data_extracted = extraction_task()
    data_transformed = data_trasnformation_task(data_extracted)
    data_loaded = data_loading_task(data_transformed)
