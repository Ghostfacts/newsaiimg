locals {
  modules_hash = md5(join("", var.modules))
  runtime_hash = md5(var.runtime)
  create_layer = length(null_resource.layer_check.triggers) > 0 ? true : false
}