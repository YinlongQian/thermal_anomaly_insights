# thermal_anomaly_insights
Last updated: April 12, 2025

This is the repo on the final project for  the Data Engineering Zoomcamp 2025.

## Problem statement



## Modules
1. IAC - Infrastructure as Code

This module uses Terraform to manage the following resources on Google Cloud Storage for usage in pipeline:
- a Google Cloud Storage bucket, for storage on:
    - raw data in CSV format
    - transformed data in PARQUET format as delta table

    Delta table is an optimized version of data lake. It provides features such as ACID transactions, schema enforcement, and time travel. Delta tables are essentially a specific type of table that is built on top of the Delta Lake storage format.

- a Google Bigquery dataset, for storage on:
    - external tables
    - staging tables
    - fact and dimension tables

- a Google Cloud Compute instance, for running the customized Airflow docker image (below)

2. AIRFLOW_DOCKER - customized Apache Airflow docker image

This module, as the workflow orchestrator, manages the DAGs in the workflow on applying the ETL process (Extract, Transform, and Load) on the raw data. It runs the workflow on the Google Cloud Compute instance spinned up by the IAC module. It has the following DAGs:
- bash_extract_dag.py - extract_raw_data

This DAG takes a list of years and a list of countries of interest and downloads the corresponding raw data from the NASA website to a temporary local folder. It adds the country field as the partition key and uploads them to the Google Cloud Storage bucket.

- spark_delta_transform_dag.py - transform_observation_data

This DAG creates a Apache Spark cluster in local mode to clean the raw data. After appling some initial data transformations, it writes the data in partitions of <year, month> as a delta table to the Google Cloud Storage bucket.

- bigquery_load_dag.py - load_delta_to_bigquery

This DAG creates an external table on the Google Cloud Bigquery based on the selected data in the delta table.




## Instruction - run pipeline
1. Prerequisites
- git, github
- Google Cloud service account
- ssh key



2. run IaC
    1. inside the local repo directory, go to folder `IAC`

        `cd IAC`

    2. open variables.tf, set the default value for the following variables:
        * client_email: your GCP service account email
        * project_name: your project name on GCP
        * (optional) region/location: all the resources will be on the same region/location
        * gcs_bucket_name: your bucker name on GCS, required to be globally unique
        * bq_dataset_name: your dataset name on Google Bigquery

    3. Copy the content in your GCP service account JSON file to `gcp_credentials.json` in subfolder `credentials`. Do not change the file name `gcp_credentials.json`.

    4. At folder `IAC`, initialize the terraform

        `terraform init`    

    5. Dry-run the terraform, check that no errors

        `terraform plan`

    6. Apply the terraform

        `terraform apply`

    7. Wait for the apply command to complete. Go to GCP console and check the bucket/dataset/instance are online


3. run Airflow
    1. s
    2. s
    

 
4. 




`docker build . --tag airflow_python310:latest`

`docker compose up -d --no-deps --build airflow-webserver airflow-scheduler`

`docker compose up airflow-init`