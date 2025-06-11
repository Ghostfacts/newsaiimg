##list of all secrects need (but requries manual entry)
resource "aws_secretsmanager_secret" "newsapi" {
  # checkov:skip=CKV2_AWS_57
  # checkov:skip=CKV_AWS_149
  name = "newsaiimg-${local.environment_map[var.environment]}-ssm-newsapi"
  tags = local.tags
}

# resource "aws_secretsmanager_secret_version" "newsapi" {
#   secret_id     = aws_secretsmanager_secret.newsapi.id
#   secret_string = data.github_actions_secrets.newsapi.secrets
# }