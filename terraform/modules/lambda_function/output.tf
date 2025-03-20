output "function" {
  value = {
    arn  = aws_lambda_function.function.arn
    name = aws_lambda_function.function.name
  }
}