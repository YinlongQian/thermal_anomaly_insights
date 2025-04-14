variable "credentials" {
  description = "Google cloud service account credentials json file"
  default     = "./credentials/gcp_credentials.json"
}

variable "client_email" {
  description = "client email of the service account"
  default     = "<your client email>"
}

variable "project_name" {
  description = "project name"
  default     = "de-zoomcampfire"
}

variable "region" {
  description = "project region"
  default     = "US"
}

variable "location" {
  description = "resource location"
  default     = "US"
}

variable "gcs_bucket_name" {
  description = "GCS bucket name"
  default     = "for_test822727"
}

variable "bq_dataset_name" {
  description = "Bigquery dataset name"
  default     = "project_dataset_1"
}