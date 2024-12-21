resource "null_resource" "make_tmp_folder" {
  provisioner "local-exec" {
    command = "mkdir /tmp/${var.layer_name}/"
  }
  triggers = {
    always_run = "${timestamp()}" #uncomment to tigger all the time    
  }
}

resource "null_resource" "pip_install" {
  # Use for_each to create one resource per module
  for_each = toset(var.modules)
  provisioner "local-exec" {
    command = "${var.runtime} -m pip install ${each.value} --no-cache-dir --upgrade --isolated --target /tmp/${var.layer_name}/python/lib/${var.runtime}/site-packages/"
  }
  triggers = {
    always_run = "${timestamp()}" #uncomment to tigger all the time
  }
  depends_on =[
    null_resource.make_tmp_folder
  ]
}

data "archive_file" "layerzip" {
    type        = "zip"
    source_dir = "/tmp/${var.layer_name}/"
    output_path = "/tmp/${var.layer_name}_package.zip"
    depends_on = [
      null_resource.make_tmp_folder,
      null_resource.pip_install
    ]
}

resource "aws_lambda_layer_version" "layer" {
    filename   = data.archive_file.layerzip.output_path
    layer_name = "${var.layer_name}"
    source_code_hash = data.archive_file.layerzip.output_base64sha256
    compatible_runtimes = [var.runtime]
    skip_destroy = true
    depends_on = [ 
      null_resource.pip_install,
      data.archive_file.layerzip
    ]
}

resource "null_resource" "Clreanup" {
  # Use for_each to create one resource per module
  for_each = toset(var.modules)
  provisioner "local-exec" {
    command = "rm -rf /tmp/${var.layer_name}*"
  }
  depends_on =[
    null_resource.pip_install,
    null_resource.make_tmp_folder,
    null_resource.pip_install,
    aws_lambda_layer_version.layer
  ]
}