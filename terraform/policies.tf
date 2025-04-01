data "aws_iam_policy_document" "lambda_policy" {
  statement {
    sid    = "SNSqueue"
    effect = "Allow"
    actions = [
      "SNS:SendMessage",
      "SQS:SendMessage"
    ]
    resources = [aws_sqs_queue.dlq.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:ListSecretVersionIds"
    ]
    resources = [aws_secretsmanager_secret.newsapi.arn]
  }
  statement {
    effect = "Allow"
    sid    = "SSMsettings"
    actions = [
      "ssm:GetParameter"
    ]
    resources = [aws_ssm_parameter.json_parameter.arn]
  }
  statement {
    sid    = "s3aibucket"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:List*",
    ]
    resources = [
      aws_s3_bucket.aiminnews.arn,
      "${aws_s3_bucket.aiminnews.arn}/*"
    ]
  }
  statement {
    sid    = "Bedrock"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"

    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-text-lite-v1",
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-text-express-v1",
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/*"
    ]
  }
}

data "aws_iam_policy_document" "step_function_policy" {
  statement {
    sid    = "lambda"
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      "${module.news_api_function.function.arn}*",
      "${module.img_gen_function.function.arn}*"
    ]
  }
  statement {
    sid    = "Bedrock"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"

    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-text-lite-v1",
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-text-express-v1",
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/*"
    ]
  }
  statement {
    sid    = "s3access"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:List*",

    ]
    resources = [
      aws_s3_bucket.aiminnews.arn,
      "${aws_s3_bucket.aiminnews.arn}/*"
    ]
  }
  statement {
    sid    = "logs"
    effect = "Allow"
    actions = [
      "logs:GetLog*",
    ]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${module.news_api_function.function.name}:*"
    ]
  }




}