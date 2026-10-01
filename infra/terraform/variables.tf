variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "dev"
}

variable "db_password" {
  default   = "adminpassword"
  sensitive = true
}
