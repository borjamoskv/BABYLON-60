variable "aws_region" {
  description = "Región criptográfica para el IAM Role de AWS"
  type        = string
  default     = "eu-west-3" # París (Latencia mínima asumida)
}

variable "github_repo" {
  description = "Repositorio autorizado para inyectar claims OIDC"
  type        = string
  default     = "borjamoskv/moskv-1-apex"
}
