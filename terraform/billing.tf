## CE cost taging (may move)
resource "aws_ce_cost_allocation_tag" "ce_project" {
  tag_key = "project"
  status  = "Active"
}

#lambda function
module "billing_function" {
  # checkov:skip=CKV_AWS_50
  # checkov:skip=CKV_AWS_272
  # checkov:skip=CKV_AWS_116
  # checkov:skip=CKV_AWS_117
  # checkov:skip=CKV_AWS_173
  source           = "./modules/lambda_function"
  nameprefex       = "newsaiimg-${local.environment_map[var.environment]}-billing_report"
  runtime          = "python3.10"
  source_path      = "files/lambdas/billing/"
  function_handler = "main.lambda_handler"
  timeout          = 830
  environment_variables = {
    PROJECT_TAG = local.tags.project,
    PROJECT_ENV = var.environment
  }
  dlq_arn       = aws_sqs_queue.dlq.arn
  attach_layers = []
  policy        = data.aws_iam_policy_document.lambda_billing_policy.json
  tags = merge(
    local.tags
  )
}

## Lambda policy
data "aws_iam_policy_document" "lambda_billing_policy" {
  statement {
    sid    = "SNSqueue"
    effect = "Allow"
    actions = [
      "SNS:Publish",
      "SQS:SendMessage"
    ]
    resources = [
      aws_sqs_queue.dlq.arn,
      aws_sns_topic.sns_topic.arn
    ]
  }
  statement {
    effect = "Allow"
    sid    = "BillingAccess"
    actions = [
      "ce:GetCostAndUsage"
    ]
    resources = ["*"]
  }
  statement {
    sid    = "s3aibucket"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:List*",
    ]
    resources = [
      aws_s3_bucket.aiminnews.arn,
      "${aws_s3_bucket.aiminnews.arn}/billing/*",
      aws_s3_bucket.website.arn,
      "${aws_s3_bucket.website.arn}/*"
    ]
  }
  statement {
    sid    = "SSMsettings"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    resources = [
      "arn:aws:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:key/alias/aws/ssm",
      aws_ssm_parameter.json_parameter.arn
    ]
  }
}
