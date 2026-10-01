output "raw_s3_bucket" {
  value = aws_s3_bucket.raw_landing_zone.bucket
}

output "rds_postgres_endpoint" {
  value = aws_db_instance.datapulse_postgres.endpoint
}

output "ecr_repository_url" {
  value = aws_ecr_repository.datapulse_app.repository_url
}
