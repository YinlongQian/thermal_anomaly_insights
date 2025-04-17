# thermal_anomaly_insights
Last updated: April 16, 2025

This is the repo on the final project for  the Data Engineering Zoomcamp 2025.

## Problem statement

Wildfires have emerged as a critical global challenge in recent years, due to climate change, land-use shifts, and other human activities. Some of the recent notable incidents that have drawn global attention includes 2023 Canadian wildfires, 2023 Maui wildfires, and 2025 California wildfires. These events cause catastrophic ecological damage, threaten human lives, and incur billions in economic losses annually.

This project looks at this problem in a broad sense. To categorize, quantify, and analyze all kinds of thermal anomalies all over the world, it utilizes the official thermal datasets captured by MODIS (Moderate Resolution Imaging Spectroradiometer) installed on NASA's satellites. At a country/region level, it classifies the detected thermal anomalies into four types: vegatation fire, volcano, other static land source, and offshore. By visualizing the trends in each type over years, it assists us to gain in-depth insights into the regional patterns related to the composing proportion, frequency, spatial extent and intensity. For instance, we will be able to identify the countries with fast-growing wildfire risks and those with more effective measures put in place. It may even be useful for policy makers to make better policies on disaster precaution, resource allocation and emergency management targeting on the most common types of thermal anomaly in the region.

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

    - a Google Cloud Compute instance, for running the customized Airflow docker image

    - a Google Cloud Compute firewall, for connecting to Airflow dashboard on the instance from local machine

2. AIRFLOW_DOCKER - customized Apache Airflow docker image

    This module, as the workflow orchestrator, manages the DAGs in the workflow on applying the ETL process (Extract, Transform, and Load) on the raw data. It runs the workflow on the Google Cloud Compute instance spinned up by the IAC module. It has the following DAGs:

    - bash_extract_dag.py - extract_raw_data

        This DAG takes a list of years and a list of countries of interest and downloads the corresponding raw data from the NASA website to a temporary local folder. It adds the country field as the partition key and uploads them to the Google Cloud Storage bucket.

    - spark_delta_transform_dag.py - transform_observation_data

        This DAG creates a Apache Spark cluster in local mode to clean the raw data. After appling some initial data transformations, it writes the data in partitions of <year, month> as a delta table to the Google Cloud Storage bucket.

    - bigquery_load_dag.py - load_delta_to_bigquery

        This DAG creates an external table on the Google Cloud BigQuery based on the selected data in the delta table.

3. dbt cloud

    This module applies further data transformation in SQL to the external table on BigQuery and builds the fact and dimension tables as the data warehouse for data visualization and data analysis. The tables are partitioned and clustered by year to make charts on Google Data Studio easily filtered on the year. As the case study reports shown below, every chart is used to analyze values in a specific year or a few specific years.

In real-life production envrionment, alternatively, I can create a cluster on Google Kubernetes Engine(GKE) and install the Airflow server application in it. Using KubernetesPodOperator in the DAGs, each step would run in a separate pod in the cluster. I can also apply a scheduler to run certains DAGs every 1 week or so. For this project, with a limited budget, I just choose to use a single Google Cloud Compute instance to run Airflow and turn it off once the jobs are done.

## Instruction - run pipeline

1. Prerequisites

    - git, (Github): for clone this repository

    - Google Cloud service account, with the following assigned roles:
        - Storage Admin
        - BigQuery Admin
        - Compute Admin
        - Service Account User

    - ssh keys: added to the Google Cloud service account above

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

3. Set-up on GCP instance

    1. ssh to the GCP instance

        ```
        ssh -i PATH_TO_PRIVATE_KEY USERNAME@EXTERNAL_IP
        ```

    2. install docker:
        ```
        # Add Docker's official GPG key:
        sudo apt-get update
        sudo apt-get install ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc

        # Add the repository to Apt sources:
        echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        ```
        ```
        sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        ```

    3. install docker compose:
        ```
        sudo apt-get update
        sudo apt-get install docker-compose-plugin
        ```

    4. pull the customized Airflow docker image from Google Artifact Registry

        ```
        sudo docker pull us-east4-docker.pkg.dev/de-zoomcampfire/airflow-for-de-zoomcamp/airflow_python310:latest
        ```

    5. clone this Github repository

        ```
        git clone https://github.com/YinlongQian/thermal_anomaly_insights.git
        ```

    6. (Optional) Edit the year list at `AIRFLOW_DOCKER/inputs/years.txt` and the country list at `AIRFLOW_DOCKER/inputs/countries.txt` of your interest

    7. build and run the customized Airflow docker image

        ```
        cd thermal_anomaly_insights/AIRFLOW_DOCKER/
        # sudo docker build . --tag airflow_python310:latest
        sudo docker image tag us-east4-docker.pkg.dev/de-zoomcampfire/airflow-for-de-zoomcamp/airflow_python310:latest airflow_python310:latest
        echo -e "AIRFLOW_UID=$(id -u)" > .env
        sudo docker compose up -d --no-deps --build airflow-webserver airflow-scheduler
        sudo docker compose up airflow-init
        ```

3. run Airflow

    1. Open the Airflow dashboard on your local machine at URL `{EXTERNAL_IP}:8080/`, where `EXTERNAL_IP` is the external IP of your GCP instance, then enter the username `airflow` and the password `airflow`.

    2. Run DAG `extract_raw_data_to_gcs`    with the following configurations:

        | configuration     | example value          |
        | --------          | -------                |
        | bucket            | bucket_name            |
        | gcs_raw_data_path | final_project/raw_data |

        With the example values above, it reads the raw data and uploads to the GCS location at `gs://bucket_name/final_project/raw_data`

    3. Run DAG `transform_raw_to_delta` with the following configurations:

        | configuration         | example value                              |
        | --------              | -------                                    |
        | input_gcs_path        | gs://bucket_name/final_project/raw_data    |
        | output_gcs_delta_path | gs://bucket_name/final_project/delta_table |

        With the example values above, it reads the raw data folder at `gs://bucket_name/final_project/raw_data`, applies the Spark transformations, and writes to the delta table at `gs://bucket_name/final_project/delta_table`.

    4. Run DAG `load_delta_to_bigquery` with the following configurations:

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

6. Clean-up resources

    1. go back to your local device, inside folder `IAC`:

        ```
        terraform destroy
        ```



