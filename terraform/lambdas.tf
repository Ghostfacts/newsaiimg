module "news_api_layer" {
  source     = "./modules/lambda_layer_python"
  layer_name = "newsaiimg-${local.environment_map[var.environment]}-lambda-layer-newsapi"
  runtime    = "python3.10"
  modules = [
    "beautifulsoup4==4.12.3",
    "requests==2.31.0"
  ]
}

module "image_gen_layer" {
  source     = "./modules/lambda_layer_python"
  layer_name = "newsaiimg-${local.environment_map[var.environment]}-lambda-layer-imggen"
  runtime    = "python3.10"
  modules = [
    "pillow==10.2.0",
    "requests==2.31.0"
  ]
}


module "news_api_function" {
  # checkov:skip=CKV_AWS_50
  # checkov:skip=CKV_AWS_272
  # checkov:skip=CKV_AWS_116
  # checkov:skip=CKV_AWS_117
  # checkov:skip=CKV_AWS_173
  source           = "./modules/lambda_function"
  nameprefex       = "newsaiimg-${local.environment_map[var.environment]}-newsapi"
  runtime          = "python3.10"
  source_path      = "files/lambdas/newsapi/"
  function_handler = "main.lambda_handler"
  timeout          = 830
  environment_variables = {
    secrect_name = aws_secretsmanager_secret.newsapi.name
    region_name  = data.aws_region.current.name
  }
  dlq_arn       = aws_sqs_queue.dlq.arn
  attach_layers = [module.news_api_layer.layer.arn]
  policy        = data.aws_iam_policy_document.lambda_policy.json
  tags = merge(
    local.tags
  )
}

module "img_gen_function" {
  # checkov:skip=CKV_AWS_50
  # checkov:skip=CKV_AWS_272
  # checkov:skip=CKV_AWS_116
  # checkov:skip=CKV_AWS_117
  # checkov:skip=CKV_AWS_173
  source                = "./modules/lambda_function"
  nameprefex            = "newsaiimg-${local.environment_map[var.environment]}-imggen"
  runtime               = "python3.10"
  source_path           = "files/lambdas/imagegen/"
  function_handler      = "main.lambda_handler"
  timeout               = 830
  environment_variables = {}
  dlq_arn               = aws_sqs_queue.dlq.arn
  attach_layers         = [module.image_gen_layer.layer.arn]
  policy                = data.aws_iam_policy_document.lambda_policy.json
  tags = merge(
    local.tags
  )
}

module "pagedeploy_function" {
  # checkov:skip=CKV_AWS_50
  # checkov:skip=CKV_AWS_272
  # checkov:skip=CKV_AWS_116
  # checkov:skip=CKV_AWS_117
  # checkov:skip=CKV_AWS_173
  source                = "./modules/lambda_function"
  nameprefex            = "newsaiimg-${local.environment_map[var.environment]}-webpagedesign"
  runtime               = "python3.10"
  source_path           = "files/lambdas/webpagedesign/"
  function_handler      = "main.lambda_handler"
  timeout               = 830
  environment_variables = {}
  dlq_arn               = aws_sqs_queue.dlq.arn
  attach_layers         = [module.image_gen_layer.layer.arn]
  policy                = data.aws_iam_policy_document.lambda_policy.json
  tags = merge(
    local.tags
  )
}
