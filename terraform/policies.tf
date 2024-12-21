data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"
    actions = [
      	"secretsmanager:GetSecretValue",
				"secretsmanager:ListSecretVersionIds"
    ]
    resources = [aws_secretsmanager_secret.newsapi.arn]
  }
}

data "aws_iam_policy_document" "step_function_policy" {
   statement {
        sid="lambda"
        Action = [
          "lambda:InvokeFunction",
        ]
        Effect = "Allow"
        Resource = "${module.news_api_function.function.arn}*"
      }
  statement{
        sid="Bedrock"
        Action = [
          "bedrock:InvokeModel",
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/*"
        ]
      }
}