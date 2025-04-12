FROM apache/airflow:latest-python3.10

USER root

# Install OpenJDK-11
RUN apt update && \
    apt-get install -y default-jdk && \
    apt-get install -y ant && \
    apt-get clean;

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64/
RUN export JAVA_HOME

# install other commands
RUN apt-get install -y wget


USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt


# gcloud CLI
RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz && \
    tar -xf google-cloud-cli-linux-x86_64.tar.gz && \
    ./google-cloud-sdk/install.sh --quiet
ENV PATH=$PATH:/opt/airflow/google-cloud-sdk/bin

RUN mkdir /opt/airflow/scripts
COPY scripts/extract_to_gcs.sh /opt/airflow/scripts/extract_to_gcs.sh