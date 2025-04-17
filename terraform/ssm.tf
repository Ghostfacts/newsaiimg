resource "aws_ssm_parameter" "json_parameter" {
  # checkov:skip=CKV2_AWS_34
  name        = "/newsaiimg/${local.environment_map[var.environment]}/settings"
  description = "Settings for the newsaiimg application"
  type        = "String"
  value = jsonencode({
    ais3bucket   = aws_s3_bucket.aiminnews.bucket
    sites3bucket = aws_s3_bucket.website.bucket
    region       = data.aws_region.current.name
    secret_name  = aws_secretsmanager_secret.newsapi.name
  })

  tags = merge(
    local.tags,
    {
      Name = "newsaiimg-${local.environment_map[var.environment]}-ssm-parameter"
    }
  )
}

##new version
resource "aws_ssm_parameter" "json_parameter_v2" {
  # checkov:skip=CKV2_AWS_34
  name        = "/newsaiimg/${local.environment_map[var.environment]}/lambdasettings"
  description = "Settings for the newsaiimg lambds"
  type        = "SecureString"
  key_id      = "alias/aws/ssm"
  value = jsonencode({
    ais3bucket    = aws_s3_bucket.aiminnews.bucket
    sites3bucket  = aws_s3_bucket.website.bucket
    region        = data.aws_region.current.name
    newsapi_token = var.newsapi_token
  })
  tags = merge(
    local.tags,
    {
      Name     = "/newsaiimg/${local.environment_map[var.environment]}/lambdasettings",
      kms_used = "builtin"
    }
  )
}