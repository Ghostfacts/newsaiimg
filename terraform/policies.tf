data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:ListSecretVersionIds"
    ]
    resources = [aws_secretsmanager_secret.newsapi.arn]
  }
  statement {
    sid    = "Bedrock"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"

    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:model/*"
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
    resources = ["${module.news_api_function.function.arn}*"]
  }
  statement {
    sid    = "Bedrock"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"

    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:model/*"
    ]
  }
}