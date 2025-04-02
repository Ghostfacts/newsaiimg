resource "aws_ssm_parameter" "json_parameter" {
  # checkov:skip=CKV2_AWS_34
  name        = "/newsaiimg/${local.environment_map[var.environment]}/settings"
  description = "Settings for the newsaiimg application"
  type        = "String"
  value = jsonencode({
    ais3bucket   = aws_s3_bucket.aiminnews.bucket
    sites3bucket = "TBD"
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