terraform {
  required_version = ">= 1.3.0"
  backend "s3" {}
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.3"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "2.7.0"
    }
  }
}
