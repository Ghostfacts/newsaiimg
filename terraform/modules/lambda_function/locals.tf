locals {
  tags          = merge(var.tags)
  lambda_name   = "${var.nameprefex}-lambda-function"
  role_name     = "${var.nameprefex}-lambda_iam_role"
  function_hash = md5(join("", var.source_path))
}