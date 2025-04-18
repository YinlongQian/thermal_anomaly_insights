terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.29.0"
    }
  }
}

provider "google" {
  # Configuration options
  credentials = file(var.credentials)
  project     = var.project_name
  region      = var.region
}

resource "google_storage_bucket" "project-bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 3
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "project-dataset" {
  dataset_id = var.bq_dataset_name
  location   = var.location
}

resource "google_compute_instance" "default" {
  name         = "vm-project"
  machine_type = "n2-standard-16"
  zone         = "us-east4-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
      size  = 30
      labels = {
        my_label = "value"
      }
    }
  }

  network_interface {
    network = "default"
    access_config {
      
    }
  }

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = var.client_email
    scopes = ["cloud-platform"]
  }
}

resource "google_compute_firewall" "rules" {
  project     = var.project_name
  name        = "for-airflow-dashboard"
  network     = "default"
  description = "Creates firewall rule on Airflow dashboard usage"

  allow {
    protocol  = "tcp"
    ports     = ["8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  # source_tags = ["foo"]
  # target_tags = ["web"]
}