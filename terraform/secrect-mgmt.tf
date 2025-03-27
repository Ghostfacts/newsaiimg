##list of all secrects need (but requries manual entry)
data "github_actions_secrets" "newsapi" {
}

resource "aws_secretsmanager_secret" "newsapi" {
  # checkov:skip=CKV2_AWS_57
  # checkov:skip=CKV_AWS_149
  name = "newsaiimg-${local.environment_map[var.environment]}-ssm-newsapi"
  tags = local.tags
}

resource "aws_secretsmanager_secret" "newsapi2" {
  # checkov:skip=CKV2_AWS_57
  # checkov:skip=CKV_AWS_149
  name = "newsaiimg-${local.environment_map[var.environment]}-ssm-newsapi2"
  tags = local.tags
}


resource "aws_secretsmanager_secret_version" "example_secret_version" {
  secret_id     = aws_secretsmanager_secret.newsapi2.id
  secret_string = data.github_actions_secrets.newsapi.secrets
}