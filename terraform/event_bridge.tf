# EventBridge Rule to trigger at 1:30 PM UTC daily
resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "daily-trigger-rule"
  description         = "Triggers the Step Function 'test' at 1:30 PM daily"
  schedule_expression = "cron(30 13 * * ? *)" # Cron for 1:30 PM UTC daily
  state               = "DISABLED"
}

# Target: Existing Step Function
resource "aws_cloudwatch_event_target" "step_function_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  arn       = aws_sfn_state_machine.newsaiimg_step_function.arn
  role_arn  = aws_iam_role.eventbridge_role.arn
}

# IAM Role for EventBridge to invoke Step Function
resource "aws_iam_role" "eventbridge_role" {
  name               = "eventbridge_step_function_role"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume_role.json
}

data "aws_iam_policy_document" "eventbridge_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

# IAM Policy for permissions to trigger Step Function
resource "aws_iam_policy" "eventbridge_policy" {
  name   = "eventbridge_policy"
  policy = data.aws_iam_policy_document.eventbridge_permissions.json
}

data "aws_iam_policy_document" "eventbridge_permissions" {
  statement {
    actions = ["states:StartExecution"]
    resources = [
      aws_sfn_state_machine.newsaiimg_step_function.arn
    ]
  }
}

resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.eventbridge_role.name
  policy_arn = aws_iam_policy.eventbridge_policy.arn
}
