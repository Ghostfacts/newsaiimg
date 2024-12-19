locals {
    tags ={
        merge(var.tags, { "runtime" = var.runtime }
        )
    }
}