##list of all secrects need (but requries manual entry)
resource "aws_secretsmanager_secret" "newsapi" {
  # checkov:skip=CKV2_AWS_57
  # checkov:skip=CKV_AWS_149
  name = "newsaiimg-${local.environment_map[var.environment]}-ssm-newsapi"
  tags = local.tags
}
