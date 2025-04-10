# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from airflow.models.param import Param
from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator

import os

from google.cloud import storage
from google.cloud import bigquery

# This DAG 
# 1. load delta table from GCS
# 2. create external table in Bigquery

# python callable task
def bigquery_create_external_table(
    bucket,
    gcs_delta_table_path,
    project,
    dataset,
    table
):
    # Set GCP credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/opt/airflow/credentials/gcp_credentials.json'

    # Set table_id to the ID of the table to create.
    external_source_format = "PARQUET"
    table_id = f"{project}.{dataset}.{table}"

    # Set the source_uris to point to your data in Google Cloud
    bucket_client = storage.Client(project).bucket(bucket)
    source_uris = [f"gs://{bucket}/{key.name}" 
                for key in bucket_client.list_blobs(prefix=gcs_delta_table_path) 
                if key.name.endswith(external_source_format.lower())]
    print(f"Total parquet files in delta table: {len(source_uris)}")


    bq_client = bigquery.Client()
    # Create ExternalConfig object with external source format
    external_config = bigquery.ExternalConfig(external_source_format)
    external_config.source_uris = source_uris

    # reference_file_schema_uri = "gs://cloud-samples-data/bigquery/federated-formats-reference-file-schema/b-twitter.avro"
    # external_config.reference_file_schema_uri = reference_file_schema_uri

    table = bigquery.Table(table_id)
    # Set the external data configuration of the table
    table.external_data_configuration = external_config
    table = bq_client.create_table(table)  # Make an API request.
    print(
        f"Created {table_id} with external source format {table.external_data_configuration.source_format}"
    )

# default values on environmental variables
default_bucket="<bucket name on Google Cloud Storage>"
default_gcs_delta_table_path="<delta table path on Google Cloud Storage>"
default_project="<project name on Google Cloud Platform>"
default_dataset="<dataset name on Google Cloud Bigquery>"
default_table="<table name on Google Cloud Bigquery>"


# environmental variables for this DAG
PARAMS = {  
    "bucket": Param(default_bucket, type="string"), 
    "gcs_delta_table_path": Param(default_gcs_delta_table_path, type="string"),
    "project": Param(default_project, type="string"), 
    "dataset": Param(default_dataset, type="string"),
    "table": Param(default_table, type="string"),
}

@dag(
    dag_id="load_delta_to_bigquery",
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
def load_delta_to_bigquery():
    python_function_args = {
        "bucket": "{{ params.bucket }}",
        "gcs_delta_table_path": "{{ params.gcs_delta_table_path }}",
        "project": "{{ params.project }}",
        "dataset": "{{ params.dataset }}",
        "table": "{{ params.table }}",
    }
    
    load_delta_to_bigquery_task = PythonOperator(
        task_id="load_delta_to_bigquery",
        python_callable=bigquery_create_external_table,
        op_kwargs=python_function_args
    )

load_delta_to_bigquery()