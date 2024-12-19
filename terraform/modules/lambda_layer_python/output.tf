output "layer" {
  value = {
    arn  = aws_lambda_layer_version.layer.arn
    name = aws_lambda_layer_version.layer.layer_name
    version = aws_lambda_layer_version.layer.version
  }
}