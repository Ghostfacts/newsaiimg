#this is the deadletterqueu for lambda and other things
resource "aws_sns_topic" "sns_topic" {
  # checkov:skip=CKV_AWS_26
  # checkov:skip=CKV_AWS_27
  name = "newsaiimg-${local.environment_map[var.environment]}-sns-topic"
}
resource "aws_sqs_queue" "dlq" {
  # checkov:skip=CKV_AWS_26
  # checkov:skip=CKV_AWS_27
  name = "newsaiimg-${local.environment_map[var.environment]}-sqs-dlq"
}

resource "aws_sns_topic_subscription" "sns_topic_subscription" {
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.dlq.arn
}

resource "aws_sns_topic_subscription" "sns_webhook_subscription" {
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = "https"
  endpoint  = var.ilert_hook
}