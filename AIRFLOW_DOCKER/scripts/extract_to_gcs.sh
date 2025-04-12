#!/bin/bash

source_base_url=https://firms.modaps.eosdis.nasa.gov/data/country/modis
local_temp_folder=/opt/airflow/raw_data

readarray -t years < /opt/airflow/inputs/years.txt
readarray -t countries < /opt/airflow/inputs/countries.txt
mkdir -p ${local_temp_folder}

for year in "${years[@]}"; do
    for country in "${countries[@]}"; do
        echo "downloading MODIS data on ${country} in ${year}..."

        # download csv from source
        csv_file=modis_${year}_${country}.csv
        source_csv_url=${source_base_url}/${year}/${csv_file}
        wget ${source_csv_url} -P ${local_temp_folder}/country=${country}

        # upload to Google Cloud Storage
        # gcloud_path=${gcs_base_path}/country=${country}/${csv_file}
        # gcloud storage cp ${local_temp_folder}/country=${country}/${csv_file} ${gcloud_path}
    done
done