output "function" {
  value = {
    arn  = aws_lambda_function.function.arn
    name = local.lambda_name
  }
}