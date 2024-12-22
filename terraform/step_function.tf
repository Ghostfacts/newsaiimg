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
  name   = "newsaiimg-${local.environment_map[var.environment]}-iam-policy-step-function"
  role   = aws_iam_role.step_function_role.id
  policy = data.aws_iam_policy_document.step_function_policy.json
}

#function it self
resource "aws_sfn_state_machine" "newsaiimg_step_function" {
  # checkov:skip=CKV_AWS_285
  name     = "newsaiimg-${local.environment_map[var.environment]}-step-function"
  role_arn = aws_iam_role.step_function_role.arn
  definition = templatefile("${path.module}/files/stepfunction_plan.json.tpl", {
    newapi_lmb_function = "${module.news_api_function.function.arn}"
  })
}