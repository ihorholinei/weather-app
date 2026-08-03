terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "y-weather-app-tf-state"
    key            = "weather-app/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    dynamodb_table = "weather-app-tf-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. ECR для Backend (FastAPI)
resource "aws_ecr_repository" "backend" {
  name                 = "weather-app-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = "production"
    Project     = "weather-app"
  }
}

# 2. ECR для Frontend (Nginx)
resource "aws_ecr_repository" "frontend" {
  name                 = "weather-app-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = "production"
    Project     = "weather-app"
  }
}

# Outputs
output "backend_ecr_url" {
  description = "URL ECR репозиторію для бэкенду"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_url" {
  description = "URL ECR репозиторію для фронтенду"
  value       = aws_ecr_repository.frontend.repository_url
}