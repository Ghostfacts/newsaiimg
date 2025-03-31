#this is the deadletterqueu for lambda and other things

resource "aws_sns_topic" "sns_topic" {
  name = "newsaiimg-${local.environment_map[var.environment]}-sns-topic"
}
resource "aws_sqs_queue" "dlq" {
  name = "newsaiimg-${local.environment_map[var.environment]}-sqs-dlq"
}

resource "aws_sns_topic_subscription" "sns_topic_subscription" {
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.dlq.arn
}
