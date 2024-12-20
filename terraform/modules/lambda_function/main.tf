data "archive_file" "function_ziped" {
    type        = "zip"
    source_dir = var.source_path
    output_path = "/tmp/${local.lambda_name}_package.zip"
}

resource "aws_lambda_function" "function" {
  function_name     = local.lambda_name
  filename          = data.archive_file.function_ziped.output_path
  source_code_hash  = data.archive_file.function_ziped.output_base64sha256
  role              = aws_iam_role.lambda_exec.arn
  handler           = var.function_handler
  runtime           = var.runtime
  timeout           = var.timeout
  memory_size       = var.memory_size
  environment {
    variables = var.environment_variables
  }
  layers = var.attach_layers
  tags = local.tags
}

resource "aws_lambda_function_event_invoke_config" "function_config" {
  function_name = aws_lambda_function.function.function_name
  maximum_retry_attempts = 2
}