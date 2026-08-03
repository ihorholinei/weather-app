terraform {
  required_version = ">= 1.5.0"
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

terraform {
  backend "s3" {
    bucket         = "y-weather-app-tf-state" # Впиши свою унікальну назву
    key            = "weather-app/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    dynamodb_table = "weather-app-tf-locks" # Таблиця для блокування стейту
  }
}


resource "aws_ecr_repository" "weather_app" {
  name                 = "weather-app-web"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = "production"
    Project     = "weather-app"
  }
}

output "ecr_repository_url" {
  description = "URL нашого ECR репозиторію"
  value       = aws_ecr_repository.weather_app.repository_url
}