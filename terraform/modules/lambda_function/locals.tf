locals {
    tags  = merge(var.tags)
    lambda_name = "${var.nameprefex}-lambda-function"
    role_name = "${var.nameprefex}-lambda_iam_role"
    policy_source = jsonencode(var.policy)
}