variable "layer_name" {
  type        = string
  description = "environment the code being deplyed"
}

variable "runtime" {
  type        = string
  description = "environment the code being deplyed"
}

variable "modules" {
  type        = list(string)
  description = "environment the code being deplyed"
}

variable "codepath" {
  type        = string
  description = "file path to custom modules to be included"
  default     = ""
}
