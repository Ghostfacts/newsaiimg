provider "aws" {
  region = "eu-west-1" # Change this to your desired region
  assume_role {
    role_arn     = "arn:aws:iam::${var.aws_account_id}:role/${var.aws_role_name}"
    session_name = "terraform"
  }
}