#Roles
resource "aws_iam_role" "step_function_role" {
  name = "step_function_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.${data.aws_region.current.name}.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "step_function_policy" {
  name = "step_function_policy"
  role = aws_iam_role.step_function_role.id

  policy = {
    Version = "2012-10-17"
    Statement = [
      {
        sid="lambda"
        Action = [
          "lambda:InvokeFunction",
        ]
        Effect = "Allow"
        Resource = "${module.news_api_function.function.arn}*"
      },
      {
        sid="Bedrock"
        Action = [
          "bedrock:InvokeModel",
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/*"
        ]
      }
    ]
  }
}





#function it self
resource "aws_sfn_state_machine" "example" {
  # checkov:skip=CKV_AWS_285
  name     = "newsaiimg-${local.environment_map[var.environment]}-step-function"
  role_arn = aws_iam_role.step_function_role.arn
  definition = templatefile("${path.module}/files/stepfunction_plan.json.tpl", {
    newapi_lmb_function = "${module.news_api_function.function.arn}"
  })
}