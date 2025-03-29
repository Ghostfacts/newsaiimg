{
  "Comment": "A Hello World example of the Amazon States Language using a Pass state",
  "StartAt": "GetNewsStories",
  "States": {
    "GetNewsStories": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "OutputPath": "$.Payload",
      "Parameters": {
        "FunctionName": "${newapi_lmb_function_arn}"
      },
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2,
          "JitterStrategy": "FULL"
        }
      ],
      "Next": "Parallel",
      "Assign": {
        "event_id.$": "$.Payload.event_id"
      }
    },
    "Parallel": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "Filtred_articles-to-s3",
          "States": {
            "Filtred_articles-to-s3": {
              "Type": "Task",
              "Parameters": {
                "ContentType": "application/json",
                "Body.$": "States.JsonToString($.all_articles)",
                "Bucket": "${s3_bucket}",
                "Key.$": "States.Format('{}/news_stories.json', $event_id)"
              },
              "Resource": "arn:aws:states:::aws-sdk:s3:putObject",
              "End": true
            }
          }
        },
        {
          "StartAt": "Get-Lambda-Logs",
          "States": {
            "Get-Lambda-Logs": {
              "Type": "Task",
              "Parameters": {
                "LogGroupName": "/aws/lambda/${newapi_lmb_function_name}",
                "LogStreamName.$": "$.logStreamName"
              },
              "Resource": "arn:aws:states:::aws-sdk:cloudwatchlogs:getLogEvents",
              "Next": "lambda_logs-to-s3"
            },
            "lambda_logs-to-s3": {
              "Type": "Task",
              "Parameters": {
                "ContentType": "application/json",
                "Body.$": "States.JsonToString($)",
                "Bucket": "${s3_bucket}",
                "Key.$": "States.Format('{}/lambda_log.json', $event_id)"
              },
              "Resource": "arn:aws:states:::aws-sdk:s3:putObject",
              "End": true
            }
          }
        }
      ],
      "ResultPath": "$.parallelResults",
      "Next": "genimage"
    },
    "genimage": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "OutputPath": "$.Payload",
      "Parameters": {
        "Payload.$": "$",
        "FunctionName": "arn:aws:lambda:eu-west-2:711387118193:function:newsaiimg-dev-imggen-lambda-function:$LATEST"
      },
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2,
          "JitterStrategy": "FULL"
        }
      ],
      "End": true
    }
  }
}