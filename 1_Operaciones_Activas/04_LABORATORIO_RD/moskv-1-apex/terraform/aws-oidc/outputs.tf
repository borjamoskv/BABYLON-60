output "iam_role_arn" {
  description = "ARN del Rol que debe ser inyectado en el Workflow de GitHub Actions"
  value       = aws_iam_role.moskv_apex_role.arn
}
