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

# 1. AWS S3 Data Lake Buckets (Raw, Staged, Curated Zones)
resource "aws_s3_bucket" "raw_landing_zone" {
  bucket        = "datapulse-raw-landing-zone-${var.environment}"
  force_destroy = true
}

resource "aws_s3_bucket" "curated_lakehouse" {
  bucket        = "datapulse-curated-lakehouse-${var.environment}"
  force_destroy = true
}

# 2. AWS RDS PostgreSQL Database Instance
resource "aws_db_instance" "datapulse_postgres" {
  allocated_storage    = 20
  max_allocated_storage = 50
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t4g.micro"
  db_name              = "datapulse"
  username             = "datapulse_admin"
  password             = var.db_password
  skip_final_snapshot  = true
  publicly_accessible = true
}

# 3. AWS ECR Container Repository
resource "aws_ecr_repository" "datapulse_app" {
  name                 = "datapulse-app"
  image_tag_mutability = "MUTABLE"
}
