locals {
  modules_hash = "${md5(join("", var.modules))}"
}
