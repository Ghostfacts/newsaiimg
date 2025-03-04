resource "null_resource" "make_tmp_folder" {
  provisioner "local-exec" {
    command = "mkdir /tmp/${var.layer_name}/"
  }
}

resource "null_resource" "pip_install" {
  # Use for_each to create one resource per module
  for_each = toset(var.modules)
  provisioner "local-exec" {
    command = "${var.runtime} -m pip install ${each.value} --no-cache-dir --upgrade --isolated --target /tmp/${var.layer_name}/python/lib/${var.runtime}/site-packages/"
  }
  depends_on = [
    null_resource.make_tmp_folder
  ]
}

data "archive_file" "layerzip" {
  type        = "zip"
  source_dir  = "/tmp/${var.layer_name}/"
  output_path = "/tmp/${var.layer_name}_package.zip"
  depends_on = [
    null_resource.make_tmp_folder,
    null_resource.pip_install
  ]
}


resource "null_resource" "layer_check" {
  triggers = {
    # always_run   = "${timestamp()}",
    runtime      = local.runtime_hash,
    modules_hash = md5(join("", var.modules))
  }
}

locals {
  create_layer = length(null_resource.layer_check.triggers) > 0 ? true : false
}


resource "aws_lambda_layer_version" "layer" {
  count               = local.create_layer ? 1 : 0
  filename            = data.archive_file.layerzip.output_path
  layer_name          = var.layer_name
  source_code_hash    = data.archive_file.layerzip.output_base64sha256
  compatible_runtimes = [var.runtime]
  skip_destroy        = true
  depends_on = [
    null_resource.pip_install,
    data.archive_file.layerzip
  ]
}
