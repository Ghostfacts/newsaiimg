output "layer" {
  value = {
    arn     = aws_lambda_layer_version.layer[0].arn
    name    = aws_lambda_layer_version.layer[0].layer_name
    version = aws_lambda_layer_version.layer[0].version
  }
}