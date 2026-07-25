# C5-REAL ULTRATHINK Autonomous Cloud Infrastructure (GCP)
# Mapeo determinista de Opciones de Nube (AlloyDB + Cloud Run + WIF)

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. BFT Ledger persistido en AlloyDB (Optimizador Columnar + pgvector)
resource "google_alloydb_cluster" "c5_ledger_cluster" {
  cluster_id = "c5-ledger-cluster"
  location   = var.region
  network    = google_compute_network.cortex_vpc.id

  initial_user {
    user     = "moskv_root"
    password = var.bft_db_password
  }
}

resource "google_alloydb_instance" "c5_ledger_primary" {
  cluster       = google_alloydb_cluster.c5_ledger_cluster.name
  instance_id   = "c5-ledger-primary"
  instance_type = "PRIMARY"

  machine_config {
    cpu_count = 8 # R7 Override: Alto rendimiento por defecto
  }
}

# 2. Orquestador de Enjambre en Cloud Run (Escalado a Cero, Serverless)
resource "google_secret_manager_secret" "cortex_bft_key_secret" {
  secret_id = "cortex-bft-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "cortex_bft_key_version" {
  secret      = google_secret_manager_secret.cortex_bft_key_secret.id
  secret_data = var.cortex_bft_key
}

resource "google_cloud_run_v2_service" "swarm_dispatcher" {
  name     = "c5-swarm-dispatcher"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    containers {
      image = "gcr.io/${var.project_id}/babylon-60-daemon:latest"

      env {
        name  = "CORTEX_BFT_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.cortex_bft_key_secret.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 50 # Sincronizado con Consolidación Masiva-Ω
    }
  }
}

# 3. VPC Nativa de CORTEX
resource "google_compute_network" "cortex_vpc" {
  name                    = "cortex-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "cortex_subnet" {
  name          = "cortex-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.cortex_vpc.id
}
