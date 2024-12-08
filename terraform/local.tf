locals {
    environment_map = {
     "development" = "dev"
     "staging"     = "stg"
     "production"  = "prod"
    }
    resource_naming_prefex="newsaiimg-${local.environment_map[var.environment]}-"
    tags={
        project = "newsaiimg"
        environment = var.environment
        required = yes
        type = "Personal-use"
    }
}