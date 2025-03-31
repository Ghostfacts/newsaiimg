resource "aws_ssm_parameter" "json_parameter" {
  name        = "newsaiimg/${local.environment_map[var.environment]}/settings"
  description = "Settings for the newsaiimg application"
  type        = "String"
  value = jsonencode({
    ais3        = aws_s3_bucket.aiminnews.bucket
    sites3      = "TBD"
    region      = data.aws_region.current.name
    secret_name = aws_secretsmanager_secret.newsapi.name
  })

  tags = merge(
    local.tags,
    {
      Name = "newsaiimg-${local.environment_map[var.environment]}-ssm-parameter"
    }
  )
}