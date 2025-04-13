# # -*- coding: utf-8 -*-
# from datetime import datetime, timedelta
# from airflow.models.param import Param
# from airflow.decorators import dag, task
# from airflow.operators.python import PythonOperator

# from pyspark.sql import SparkSession
# from pyspark.sql import functions as F
# from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
# import pandas as pd

# # This DAG 
# # 1. load raw observation data from AWS S3
# # 2. apply data cleaning on raw data
# # 3. write to AWS S3 as a delta table for downstream tasks


# # python callable task
# def spark_observation_delta(
#     aws_access_key_id,
#     aws_secret_access_key,
#     input_s3_path,
#     output_s3_delta_path
# ):
#     print("********* Arguments **********")
#     print(f"{aws_access_key_id=}")
#     print(f"{aws_secret_access_key=}")
#     print(f"{input_s3_path=}")
#     print(f"{output_s3_delta_path=}")
#     print("********* Arguments **********")


#     spark = (
#         SparkSession.builder.appName("process_observation_data").master("local[*]")
#         .config("spark.jars.packages", "io.delta:delta-core_2.12:2.3.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
#         .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id)
#         .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key)
#         # .config("spark.hadoop.fs.s3a.session.token", aws_session_token) # optional
#         # .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
#         # .config("spark.hadoop.fs.s3a.endpoint", "s3.us-east-1.amazonaws.com")
#         .config("spark.hadoop.fs.s3a.path.style.access", "true")
#         .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') # for delta table
#         .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') # for delta table
#         .config("spark.sql.parquet.compression.codec", "zstd")
#         .config("spark.sql.parquet.compression.codec.zstd.level", 3)
#         .config("spark.sql.parquet.outputTimestampType", "TIMESTAMP_MILLIS")
#         .config("spark.sql.session.timeZone", "+00:00")
#         .config("spark.hadoop.parquet.writer.version", "v2")
#         .getOrCreate()  
#     )
#     raw_df = spark.read.csv(
#         input_s3_path, header=True, inferSchema=True
#     )
#     print("read_spark")
#     print(raw_df.show())

#     def pandas_clean_data(key, pdf):
#         pdf['acq_timestamp'] = pd.to_datetime(pdf['acq_date'].astype('str') + ' ' + 
#                                             (pdf['acq_time'] // 100).astype('str') + ':' + 
#                                             (pdf['acq_time'] % 100).astype('str') + ':00')
#         pdf['country'] = pdf['country'].str.replace("_", " ")

#         return pdf[
#             ['latitude', 'longitude', 'brightness', 'scan', 'track', 'acq_timestamp', 
#             'satellite', 'instrument', 'confidence', 'version', 'bright_t31', 'frp', 'daynight', 'type', 'country']
#         ]

#     observation_schema = StructType([
#         StructField('latitude', DoubleType(), True),
#         StructField('longitude', DoubleType(), True),
#         StructField('brightness', DoubleType(), True),
#         StructField('scan', DoubleType(), True),
#         StructField('track', DoubleType(), True),
#         StructField('acq_timestamp', TimestampType(), True),
#         StructField('satellite', StringType(), True),
#         StructField('instrument', StringType(), True),
#         StructField('confidence', IntegerType(), False),
#         StructField('version', DoubleType(), True),
#         StructField('bright_t31', DoubleType(), True),
#         StructField('frp', DoubleType(), True),
#         StructField('daynight', StringType(), True),
#         StructField('type', IntegerType(), False),
#         StructField('country', StringType(), True),
#     ]) 
#     observation_df = (
#         raw_df
#         # .repartition("country") 
#         # .sortWithinPartitions(['country', 'timestamp'])
#         .groupBy("country")
#         .applyInPandas(pandas_clean_data, schema = observation_schema)
#     )

#     observation_df = observation_df.withColumn('year', F.year(observation_df['acq_timestamp']))
#     observation_df = observation_df.withColumn('month', F.month(observation_df['acq_timestamp']))
#     # observation_df = observation_df.withColumn('day', F.dayofmonth(observation_df['acq_timestamp']))

#     observation_df.write \
#         .format("delta") \
#         .partitionBy(["year", "month"]) \
#         .option('fs.s3a.committer.name', 'partitioned') \
#         .option('fs.s3a.committer.staging.conflict-mode', 'replace') \
#         .option("fs.s3a.fast.upload.buffer", "bytebuffer") \
#         .mode("append") \
#         .save(output_s3_delta_path)

#     spark.stop()


# # default values on environmental variables
# default_aws_access_key_id="<AWS key>"
# default_aws_secret_access_key="<AWS secret key>"
# default_input_s3_path="<AWS S3 path on raw temporal anomaly observation data>"
# default_output_s3_delta_path="<AWS S3 path on delta table destination >"

# # environmental variables for this DAG
# PARAMS = {
#     # AWS credentials    
#     "aws_access_key_id": Param(default_aws_access_key_id, type="string"), 
#     "aws_secret_access_key": Param(default_aws_secret_access_key, type="string"),
#     "input_s3_path": Param(default_input_s3_path, type="string"), 
#     "output_s3_delta_path": Param(default_output_s3_delta_path, type="string"),
# }

# @dag(
#     dag_id="transform_raw_to_delta",
#     max_active_runs=1, 
#     start_date = datetime(2024, 1, 1),
#     catchup = False, 
#     schedule_interval = None, 
#     is_paused_upon_creation = False, 
#     render_template_as_native_obj=True,
#     params = PARAMS,  
#     default_args={
#         "retries": 0,
#         "retry_delay": timedelta(seconds=10)
#     },
# )
# def transform_observation_data():
#     python_function_args = {
#         "aws_access_key_id": "{{ params.aws_access_key_id }}",
#         "aws_secret_access_key": "{{ params.aws_secret_access_key }}",
#         "input_s3_path": "{{ params.input_s3_path }}",
#         "output_s3_delta_path": "{{ params.output_s3_delta_path }}",
#     }
    
#     transform_observation_data_task = PythonOperator(
#         task_id="transform_observation_data",
#         python_callable=spark_observation_delta,
#         op_kwargs=python_function_args
#     )

# transform_observation_data()