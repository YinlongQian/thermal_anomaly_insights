# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from airflow.models.param import Param
from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator

from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import pandas as pd

# This DAG 
# 1. load raw observation data from AWS S3
# 2. apply data cleaning on raw data
# 3. write to AWS S3 as a delta table for downstream tasks


# python callable task
def spark_observation_delta(
    input_gcs_path,
    output_gcs_delta_path,
):
    gcp_credentials_location = "/opt/airflow/credentials/gcp_credentials.json"
    gcs_connector_jar_file = "/opt/airflow/jars/gcs-connector-hadoop3-latest.jar"

    conf = SparkConf() \
        .setMaster('local[*]') \
        .setAppName('transform_data_to_delta') \
        .set('spark.driver.memory', '15g') \
        .set("spark.jars", gcs_connector_jar_file) \
        .set("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
        .set("spark.jars.packages", "io.delta:delta-core_2.12:2.3.0") \
        .set('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') \
        .set('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') \
        .set("spark.sql.parquet.compression.codec", "zstd") \
        .set("spark.sql.parquet.compression.codec.zstd.level", 3) \
        .set("spark.sql.parquet.outputTimestampType", "TIMESTAMP_MILLIS") \
        .set("spark.sql.session.timeZone", "+00:00") \
        .set("spark.hadoop.parquet.writer.version", "v2")
        # .set("spark.jars.packages", "com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.26") \
        # .set("spark.hadoop.google.cloud.auth.service.account.json.keyfile", gcp_credentials_location)

    sc = SparkContext(conf=conf)
    hadoop_conf = sc._jsc.hadoopConfiguration()
    # hadoop_conf.set("fs.gs.auth.service.account.private.key.id", privateKeyId)
    # hadoop_conf.set("fs.gs.auth.service.account.private.key", privateKey)
    # hadoop_conf.set("fs.gs.auth.service.account.email", clientEmail)
    hadoop_conf.set("fs.gs.auth.service.account.json.keyfile", gcp_credentials_location)
    hadoop_conf.set("fs.AbstractFileSystem.gs.impl",  "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")
    hadoop_conf.set("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
    hadoop_conf.set("fs.gs.auth.service.account.enable", "true")

    spark = SparkSession.builder \
        .config(conf=sc.getConf()) \
        .getOrCreate()
    

    raw_df = spark.read.csv(
        input_gcs_path, header=True, inferSchema=True
    )

    def pandas_clean_data(key, pdf):
        pdf['acq_timestamp'] = pd.to_datetime(pdf['acq_date'].astype('str') + ' ' + 
                                            (pdf['acq_time'] // 100).astype('str') + ':' + 
                                            (pdf['acq_time'] % 100).astype('str') + ':00')

        return pdf[
            ['latitude', 'longitude', 'brightness', 'scan', 'track', 'acq_timestamp', 
            'satellite', 'instrument', 'confidence', 'version', 'bright_t31', 'frp', 'daynight', 'type', 'country']
        ]

    observation_schema = StructType([
        StructField('latitude', DoubleType(), True),
        StructField('longitude', DoubleType(), True),
        StructField('brightness', DoubleType(), True),
        StructField('scan', DoubleType(), True),
        StructField('track', DoubleType(), True),
        StructField('acq_timestamp', TimestampType(), True),
        StructField('satellite', StringType(), True),
        StructField('instrument', StringType(), True),
        StructField('confidence', IntegerType(), False),
        StructField('version', DoubleType(), True),
        StructField('bright_t31', DoubleType(), True),
        StructField('frp', DoubleType(), True),
        StructField('daynight', StringType(), True),
        StructField('type', IntegerType(), False),
        StructField('country', StringType(), True),
    ]) 
    observation_df = (
        raw_df
        # .repartition("country") 
        # .sortWithinPartitions(['country', 'timestamp'])
        .groupBy("country")
        .applyInPandas(pandas_clean_data, schema = observation_schema)
    )

    observation_df = observation_df.withColumn('year', F.year(observation_df['acq_timestamp']))
    observation_df = observation_df.withColumn('month', F.month(observation_df['acq_timestamp']))
    # observation_df = observation_df.withColumn('day', F.dayofmonth(observation_df['acq_timestamp']))

    observation_df \
        .repartition("year", "month") \
        .write \
        .format("delta") \
        .partitionBy(["year", "month"]) \
        .mode("append") \
        .save(output_gcs_delta_path)

    spark.stop()


# default values on environmental variables
default_input_gcs_path="<GCS path on raw data>"
default_output_gcs_delta_path="<GCS path on delta table destination>"

# environmental variables for this DAG
PARAMS = {
    # GCP credentials    
    "input_gcs_path": Param(default_input_gcs_path, type="string"), 
    "output_gcs_delta_path": Param(default_output_gcs_delta_path, type="string"),
}

@dag(
    dag_id="transform_raw_to_delta",
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
def transform_observation_data():
    python_function_args = {
        "input_gcs_path": "{{ params.input_gcs_path }}",
        "output_gcs_delta_path": "{{ params.output_gcs_delta_path }}",
    }
    
    transform_observation_data_task = PythonOperator(
        task_id="transform_observation_data",
        python_callable=spark_observation_delta,
        op_kwargs=python_function_args
    )

transform_observation_data()