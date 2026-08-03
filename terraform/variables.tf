variable "aws_region" {
  description = "AWS регіон для деплою"
  type        = string
  default     = "eu-central-1"
}

variable "db_password" {
  description = "Master password for the RDS Postgres instance"
  type        = string
  sensitive   = true
}