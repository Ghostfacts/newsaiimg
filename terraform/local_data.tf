locals {
  environment_map = {
    "development" = "dev"
    "staging"     = "stg"
    "production"  = "prod"
  }
  region_map = {
    "eu-west-1"    = "dub",
    "eu-west-2"    = "lon",
    "eu-west-3"    = "par",
    "eu-central-1" = "fra",
    "us-east-1"    = "nyc"
  }
  resource_naming_prefex = "newsaiimg-${local.environment_map[var.environment]}-${local.region_map[data.aws_region.current.name]}-"
  tags = {
    project     = "newsaiimg"
    environment = var.environment
    region      = local.region_map[data.aws_region.current.name]
  }
}

data "aws_region" "current" {}