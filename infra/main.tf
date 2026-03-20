terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "semantic-canvas-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── VPC ───

resource "google_compute_network" "main" {
  name                    = "semantic-canvas-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "main" {
  name          = "semantic-canvas-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
}

# VPC Connector for Cloud Run → private services
resource "google_vpc_access_connector" "connector" {
  name          = "sc-vpc-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.main.name
}

# ─── Cloud SQL (PostgreSQL + pgvector) ───

resource "google_sql_database_instance" "postgres" {
  name             = "semantic-canvas-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"

    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "app" {
  name     = "semantic_canvas"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = "canvas"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# ─── Memorystore Redis ───

resource "google_redis_instance" "cache" {
  name           = "semantic-canvas-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.main.id

  redis_version = "REDIS_7_0"
}

# ─── Artifact Registry ───

resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "semantic-canvas"
  format        = "DOCKER"
}

# ─── Cloud Tasks Queue ───

resource "google_cloud_tasks_queue" "ingestion" {
  name     = "semantic-canvas-ingestion"
  location = var.region

  retry_config {
    max_attempts       = 3
    min_backoff        = "10s"
    max_backoff        = "300s"
    max_doublings      = 3
  }

  rate_limits {
    max_concurrent_dispatches = 5
    max_dispatches_per_second = 1
  }
}

# ─── Service Accounts ───

resource "google_service_account" "api" {
  account_id   = "sc-api"
  display_name = "Semantic Canvas API"
}

resource "google_service_account" "ingestion" {
  account_id   = "sc-ingestion"
  display_name = "Semantic Canvas Ingestion"
}

# API can enqueue Cloud Tasks
resource "google_cloud_tasks_queue_iam_member" "api_enqueue" {
  name     = google_cloud_tasks_queue.ingestion.id
  role     = "roles/cloudtasks.enqueuer"
  member   = "serviceAccount:${google_service_account.api.email}"
  location = var.region
}

# API can access secrets
resource "google_project_iam_member" "api_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Ingestion can access secrets
resource "google_project_iam_member" "ingestion_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}

# ─── Secret Manager ───

resource "google_secret_manager_secret" "db_password" {
  secret_id = "sc-db-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

# ─── Cloud Run: API ───

resource "google_cloud_run_v2_service" "api" {
  name     = "semantic-canvas-api"
  location = var.region

  template {
    service_account = google_service_account.api.email

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/semantic-canvas/api:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql://canvas:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/semantic_canvas"
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
      }
      env {
        name  = "TASK_QUEUE_BACKEND"
        value = "cloud_tasks"
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "CLOUD_TASKS_QUEUE"
        value = google_cloud_tasks_queue.ingestion.name
      }
      env {
        name  = "CLOUD_TASKS_LOCATION"
        value = var.region
      }
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = 10
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (API handles its own auth)
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ─── Cloud Run Job: Ingestion ───

resource "google_cloud_run_v2_job" "ingestion" {
  name     = "semantic-canvas-ingestion"
  location = var.region

  template {
    template {
      service_account = google_service_account.ingestion.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/semantic-canvas/ingestion:latest"

        resources {
          limits = {
            cpu    = "2"
            memory = "4Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = "postgresql://canvas:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/semantic_canvas"
        }
      }

      timeout = "600s"
      max_retries = 1
    }
  }
}

# ─── Outputs ───

output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "db_private_ip" {
  value = google_sql_database_instance.postgres.private_ip_address
}

output "redis_host" {
  value = google_redis_instance.cache.host
}
