# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from airflow.models.param import Param
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

import os
from pathlib import Path

from google.cloud import storage


# This DAG 
# 1. extract raw data from source
# 2. upload data to Google Cloud Storage


# python callable task
def upload_to_gcs(
    bucket,
    gcs_raw_data_path
):
    source_directory="/opt/airflow/raw_data"
    directory_as_path_obj = Path(source_directory)
    paths = directory_as_path_obj.rglob("*")
    file_paths = [path for path in paths if path.is_file() and path.name.endswith('csv')]
    relative_paths = [path.relative_to(source_directory) for path in file_paths]
    string_paths = [str(path) for path in relative_paths]

    # Set GCP credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/opt/airflow/credentials/gcp_credentials.json'

    bucket = storage.Client().bucket(bucket)

    print("Uploading raw data to GCS...")
    for string_path in string_paths:
        source_file_name = f"{source_directory}/{string_path}"
        destination_blob_name = f"{gcs_raw_data_path}/{string_path}"
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)
        print(f"Uploaded {source_file_name} to {destination_blob_name}")
    print(f"{len(string_paths)} csv files uploaded")

# default values on environmental variables
default_bucket="<bucket name on Google Cloud Storage>"
default_gcs_raw_data_path="<path for raw data on Google Cloud Storage>"

# environmental variables for this DAG
PARAMS = {  
    "bucket": Param(default_bucket, type="string"), 
    "gcs_raw_data_path": Param(default_gcs_raw_data_path, type="string"),
}

@dag(
    dag_id="extract_raw_data_to_gcs",
    max_active_runs=1, 
    start_date = datetime(2024, 1, 1),
    catchup = False, 
    schedule_interval = None, 
    is_paused_upon_creation = False, 
    render_template_as_native_obj=True,
    params = PARAMS,  
    default_args={
        "retries": 0,
        "retry_delay": timedelta(seconds=10)
    },
)
def extract_raw_data():
    python_function_args = {
        "bucket": "{{ params.bucket }}",
        "gcs_raw_data_path": "{{ params.gcs_raw_data_path }}",
    }

    download_raw_data_task = BashOperator(
        task_id="download_raw_data",
        bash_command="bash /opt/airflow/scripts/extract_to_gcs.sh "
    )

    upload_raw_data_to_gcs_task = PythonOperator(
        task_id="upload_raw_data_to_gcs",
        python_callable=upload_to_gcs,
        op_kwargs=python_function_args
    )

    upload_raw_data_to_gcs_task.set_upstream(download_raw_data_task)


extract_raw_data()