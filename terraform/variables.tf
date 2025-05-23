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

variable "ilert_token" {
  type        = string
  default     = "Need to be changed before can run"
  description = "ilert token for alerting"
  sensitive   = true
}

variable "newsapi_token" {
  type        = string
  description = "This token is used to access the newsapi service"
  sensitive   = true
}

variable "openai_token" {
  type        = string
  description = "This token is used to access the newsapi service"
  sensitive   = true
}

variable "openai_project" {
  type        = string
  description = "the openAI project"
  sensitive   = true
}

variable "openai_org" {
  type        = string
  description = "the openAI org"
  sensitive   = true
}