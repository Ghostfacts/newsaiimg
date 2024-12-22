locals {
  modules_hash = "${md5(join("", var.modules))}"
  runtime_hash = "${md5(var.runtime)}"
  combined_hash = "${md5(modules_hash ~ runtime_hash)}"
}
