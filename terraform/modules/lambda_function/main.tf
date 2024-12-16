data "archive_file" "function_ziped" {
    type        = "zip"
    source_dir = var.source_path
    output_path = "/tmp/${var.name}_package.zip"
}

resource "aws_lambda_function" "function" {
  function_name     = var.name
  filename          = data.archive_file.function_ziped.output_path
  source_code_hash  = data.archive_file.function_ziped.output_base64sha256
  role              = aws_iam_role.lambda_exec.arn
  handler           = var.function_handler
  runtime           = var.runtime
  timeout           = 10
  memory_size       = 128
}