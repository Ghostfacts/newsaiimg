locals {
  modules_hash = "${md5(join("", var.modules))}",
  runtime_hash = "${md5(var.runtime)}",
}
