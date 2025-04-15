# thermal_anomaly_insights
Last updated: April 12, 2025

This is the repo on the final project for  the Data Engineering Zoomcamp 2025.

## Problem statement



## Modules

![image_alt](https://github.com/YinlongQian/thermal_anomaly_insights/blob/main/Project-DAG.png?raw=true)


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

        ```
        cd IAC
        ```

    2. open variables.tf, set the default value for the following variables:
        * client_email: your GCP service account email
        * project_name: your project name on GCP
        * (optional) region/location: all the resources will be on the same region/location
        * gcs_bucket_name: your bucker name on GCS, required to be globally unique
        * bq_dataset_name: your dataset name on Google Bigquery

    3. Copy the content in your GCP service account JSON file to `gcp_credentials.json` in subfolder `credentials`. Do not change the file name `gcp_credentials.json`.

    4. At folder `IAC`, initialize terraform, dry-run terraform, and apply terraform

        ```
        terraform init
        terraform plan
        terraform apply
        ```

    5. Wait for the apply command to complete. Go to GCP console and check the bucket/dataset/instance are online


3. run Airflow
    1. ssh to the GCP instance

        ```
        ssh -i PATH_TO_PRIVATE_KEY USERNAME@EXTERNAL_IP
        ```

    2. clone this Github repository

        ```
        git clone https://github.com/YinlongQian/thermal_anomaly_insights.git
        ```

    3. build and run the Airflow docker image

        ```
        cd AIRFLOW_DOCKER
        docker build . --tag airflow_python310:latest
        docker compose up -d --no-deps --build airflow-webserver airflow-scheduler
        docker compose up airflow-init
        ```

    4. (Optional) Edit the year list at `inputs/years.txt` and the country list at `inputs/countries.txt` of your interest

    5. Open the Airflow dashboard at `http://localhost:8080/`, enter the username `airflow` and the password `airflow`

    6. Run DAG `extract_raw_data_to_gcs`    with the following configurations:

        | configuration     | example value          |
        | --------          | -------                |
        | bucket            | bucket_name            |
        | gcs_raw_data_path | final_project/raw_data |

        With the example values above, it reads the raw data and uploads to the GCS location at `gs://bucket_name/final_project/raw_data`

    7. Run DAG `transform_raw_to_delta` with the following configurations:

        | configuration         | example value                              |
        | --------              | -------                                    |
        | input_gcs_path        | gs://bucket_name/final_project/raw_data    |
        | output_gcs_delta_path | gs://bucket_name/final_project/delta_table |

        With the example values above, it reads the raw data folder at `gs://bucket_name/final_project/raw_data`, applies the Spark transformations, and writes to the delta table at `gs://bucket_name/final_project/delta_table`.

    8. Run DAG `load_delta_to_bigquery` with the following configurations:

        | configuration        | example value               |
        | --------             | -------                     |
        | bucket               | bucket_name                 |
        | gcs_delta_table_path | final_project/delta_table   |
        | project              | project_name                |
        | dataset              | dataset_name                |
        | table                | table_name                  |

        With the example values above, it reads the delta table at `gs://bucket_name/final_project/delta_table`, and loads to the Biqquery external table `project_name.dataset_name.table_name`.


 
4. run dbt Cloud

    1. Open dbt Lab at `https://www.getdbt.com/`. Log in your dbt account and connect to your Github/Gitlab account if you have not done so.

    2. Create a project. Set `Development connection` to your Bigquery by `Upload a Service Account JSON file`. Clone this Github repository to your Github/Gitlab account, and set `Repository` to the cloned repository.

        Please see `DE Zoomcamp 4.2.1 - Start Your dbt Project Bigquery and dbt Cloud (Alternative A)` in `Module 4: Analytics Engineering` for details on creating a deployment environment.

    3. Create a deployment environment. Set `Environment type` to `Deployment`, set `deployment type` to `Production`, and click `Save`. Set the following `Environment variables`:

        | Key          | Production   | Description                                                                     |
        | --------     | -------      | -------                                                                         |
        | DBT_DATABASE | project_name | your GCP project                                                                |
        | DBT_SCHEMA   | dataset_name | your Bigquery dataset that stores the external table generated by the DAG above |

        Please see `DE Zoomcamp 4.4.1 - Deployment Using dbt Cloud (Alternative A)` in `Module 4: Analytics Engineering` for details on creating a deployment environment.

    4. Create a job. Click `Create Job` then select `Deploy job`. Set `Job name` and select the deployment environment. Click `Save`.

    5. Go to the jobs page and select the job created. Click `Run now`.

    6. After run completes, go to Bigquery dashboard and verify the table `fact_observations` is in the dataset set above as an environmental variable.

5. Visualization - Google Data Studio

    1. Open Google Data Studio at `https://lookerstudio.google.com/`.

    2. Create `Data Source`. Select `BigQuery`. Find table `fact_observations` in the project/dataset. Click `CONNECT`.

    3. Create `Report`. Switch to `My data source` and select `fact_observations`. `Add` to the report.

    4. Create a case study of a country by adding charts.

        You can find some case study reports at folder Data_Studio_reports:

        [Case study - Indonesia](https://github.com/YinlongQian/thermal_anomaly_insights/blob/main/Data_Studio_reports/Case_Study-Indonesia.pdf)

        [Case study - United States](https://github.com/YinlongQian/thermal_anomaly_insights/blob/main/Data_Studio_reports/Case_Study-United_States.pdf)

        



