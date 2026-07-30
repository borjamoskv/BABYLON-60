variable "project_id" {
  type        = string
  description = "GCP Project ID para CORTEX"
  default     = "cortex-babylon-60"
}

variable "region" {
  type        = string
  description = "Región termodinámica de ejecución"
  default     = "europe-west1"
}

variable "bft_db_password" {
  type        = string
  description = "Master BFT Password"
  sensitive   = true
}

variable "cortex_bft_key" {
  type        = string
  description = "Llave criptográfica de anclaje BFT"
  sensitive   = true
}
