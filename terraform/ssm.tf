resource "aws_ssm_parameter" "json_parameter" {
  # checkov:skip=CKV2_AWS_34
  name        = "/newsaiimg/${local.environment_map[var.environment]}/settings"
  description = "Settings for the newsaiimg lambds"
  type        = "SecureString"
  key_id      = "alias/aws/ssm"
  value = jsonencode({
    ais3bucket     = aws_s3_bucket.aiminnews.bucket
    sites3bucket   = aws_s3_bucket.website.bucket
    region         = data.aws_region.current.name
    newsapi_token  = var.newsapi_token
    openai_token   = var.openai_token
    openai_project = var.openai_project
    openai_org     = var.openai_org
  })
  tags = merge(
    local.tags,
    {
      Name     = "/newsaiimg/${local.environment_map[var.environment]}/settings",
      kms_used = "builtin"
    }
  )
}