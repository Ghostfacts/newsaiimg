locals {
  tags          = merge(var.tags)
  lambda_name   = "${var.nameprefex}-lambda-function"
  role_name     = "${var.nameprefex}-lambda_iam_role"
  files         = [for file in fileset(var.source_path, "**/*") : file]
  function_hash = md5(join("", [for file in local.files : filemd5(file)]))
}