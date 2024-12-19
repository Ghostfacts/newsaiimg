module "news_api_layer" {
  source = "./modules/lambda_layer_python"
  layer_name = "newsaiimg-${local.environment_map[var.environment]}-lambda-layer-newsapi"
  runtime = "python3.10"
  modules = [
    "newsapi==0.1.1",
    "newsapi-python==0.2.7",
    "beautifulsoup4==4.12.3",
    "requests==2.31.0"
  ]
}

module "news_api_function" {
  source = "./modules/lambda_function"
  name = "newsaiimg-${local.environment_map[var.environment]}-lambda-function-newsapi"
  runtime = "python3.10"
  source_path = "files/lambdas/newsapi/"
  function_handler = "main.lambda_handler"
  environment_variables ={
    secrect_name = aws_secretsmanager_secret.newsapi.name
  }
  tags = merge(
    local.tags,
  {
    Name = "newsaiimg-${local.environment_map[var.environment]}-lambda-function-newsapi"
  }
  )
}