variable "aws_account_id" {
  type        = string
  description = "Account Nubmer to deploy in"
}

variable "aws_role_name" {
  type        = string
  description = "Role to deploy with"
}

variable "environment" {
  type        = string
  description = "environment the code being deplyed"
}

variable "github_token" {
  type        = string
  description = "github auth token"
}


