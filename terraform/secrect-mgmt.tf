##list of all secrects need (but requries manual entry)
resource "aws_secretsmanager_secret" "newsapi" {
  name = "newsaiimg-${local.environment_map[var.environment]}-ssm-newsapi"
}
