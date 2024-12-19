variable "nameprefex" {
  type       = string
  description = "Name of the Function"  
}



variable "runtime" {
  type       = string
  description = "runtime to use"  
}

variable "source_path" {
  type       = string
  description = "path to code"  
}

variable "function_handler" {
  type       = string
  description = "hadlecoes"  
}

variable "tags" {
  type       = any
  description = "hadlecoes"  
}

variable "environment_variables" {
  type       = any
  description = "hadlecoes"  
}
