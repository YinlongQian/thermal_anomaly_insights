# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from airflow.models.param import Param
from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import pandas as pd

# This DAG 
# 1. load raw observation data from AWS S3
# 2. apply data cleaning on raw data
# 3. write to AWS S3 as a delta table for downstream tasks


# python callable task
def spark_observation_delta(
    aws_access_key_id,
    aws_secret_access_key,
    input_s3_path,
    output_s3_delta_path
):
    from os import listdir
    from os.path import isfile, join

    mypath = "/opt/airflow/credentials"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    print(onlyfiles)
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%")


# default values on environmental variables
default_aws_access_key_id="<AWS key>"
default_aws_secret_access_key="<AWS secret key>"
default_input_s3_path="<AWS S3 path on raw temporal anomaly observation data>"
default_output_s3_delta_path="<AWS S3 path on delta table destination >"

# environmental variables for this DAG
PARAMS = {
    # AWS credentials    
    "aws_access_key_id": Param(default_aws_access_key_id, type="string"), 
    "aws_secret_access_key": Param(default_aws_secret_access_key, type="string"),
    "input_s3_path": Param(default_input_s3_path, type="string"), 
    "output_s3_delta_path": Param(default_output_s3_delta_path, type="string"),
}

@dag(
    dag_id="test_dag_run",
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
def clean_observation_data():
    python_function_args = {
        "aws_access_key_id": "{{ params.aws_access_key_id }}",
        "aws_secret_access_key": "{{ params.aws_secret_access_key }}",
        "input_s3_path": "{{ params.input_s3_path }}",
        "output_s3_delta_path": "{{ params.output_s3_delta_path }}",
    }
    
    clean_observation_data_task = PythonOperator(
        task_id="clean_observation_data_task_id",
        python_callable=spark_observation_delta,
        op_kwargs=python_function_args
    )

clean_observation_data()