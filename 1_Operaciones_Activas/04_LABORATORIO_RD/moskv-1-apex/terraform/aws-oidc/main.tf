terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Proveedor OIDC de GitHub
resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["1b511abead59c6ce207077c0bf0e0043b1382612"] # Certificado base de GitHub
}

# Rol IAM asumible vía JWT desde GitHub Actions (Self-Hosted Runner)
resource "aws_iam_role" "moskv_apex_role" {
  name = "moskv-1-apex-runner-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com",
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:ref:refs/heads/master"
          }
        }
      }
    ]
  })
}

# Política estricta: Sólo lectura en KMS y S3 (Membrana Zero-Trust)
resource "aws_iam_role_policy" "moskv_apex_policy" {
  name = "moskv-1-apex-strict-policy"
  role = aws_iam_role.moskv_apex_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "kms:Decrypt"
        ]
        Resource = "*"
      }
    ]
  })
}
