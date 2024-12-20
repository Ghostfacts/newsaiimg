data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = local.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy" "inline_policy" {
  name   = "inline_policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.merged_policy.json
}

data "aws_iam_policy_document" "merged_policy" {
  source_json = local.policy_source
}
