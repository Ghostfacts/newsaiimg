resource "null_resource" "pip" {
  for_each = toset(var.modules)
  provisioner "local-exec" {
    command = <<EOT
    ${var.runtime} -m pip install ${each.value} --no-cache-dir --upgrade --isolated --target /tmp/${var.layer_name}/python/lib/${var.runtime}/site-packages/
    EOT
  }
  triggers = {
    time = timestamp()
  }
}

data "archive_file" "layerzip" {
  type        = "zip"
  source_dir  = "/tmp/${var.layer_name}/"
  output_path = "/tmp/${var.layer_name}_package.zip"
  depends_on = [
    null_resource.pip
  ]
}

resource "aws_lambda_layer_version" "layer" {
  filename            = data.archive_file.layerzip.output_path
  layer_name          = var.layer_name
  source_code_hash    = data.archive_file.layerzip.output_base64sha256
  compatible_runtimes = [var.runtime]
  skip_destroy        = true
  depends_on = [
    data.archive_file.layerzip
  ]
}
