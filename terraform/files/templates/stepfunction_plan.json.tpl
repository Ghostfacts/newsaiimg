{
  "Comment": "A Hello World example of the Amazon States Language using a Pass state",
  "StartAt": "GetNewsStories",
  "States": {
    "GetNewsStories": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "OutputPath": "$.Payload",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:${ region }:${ accountid }:function:newsaiimg-${ environment }-newsapi-lambda-function"
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
      "Next": "Generating_image",
      "Assign": {
        "event_id.$": "$.Payload.event_id"
      }
    },
    "Generating_image": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "Waitforai",
          "States": {
            "Waitforai": {
              "Type": "Wait",
              "Seconds": 200,
              "Next": "genimage"
            },
            "genimage": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "FunctionName": "arn:aws:lambda:${ region }:${ accountid }:function:newsaiimg-${ environment }-imggen-lambda-function:$LATEST",
                "Payload": {
                  "event_id.$": "$event_id"
                }
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
        },
        {
          "StartAt": "Get-newsapi-Logs",
          "States": {
            "Get-newsapi-Logs": {
              "Type": "Task",
              "Parameters": {
                "LogGroupName": "/aws/lambda/newsaiimg-${ environment }-newsapi-lambda-function",
                "LogStreamName.$": "$.logStreamName"
              },
              "Resource": "arn:aws:states:::aws-sdk:cloudwatchlogs:getLogEvents",
              "Next": "Newsapi-Logs-to-s3"
            },
            "Newsapi-Logs-to-s3": {
              "Type": "Task",
              "Parameters": {
                "ContentType": "application/json",
                "Body.$": "States.JsonToString($)",
                "Bucket": "newsaiimg-${ environment }-s3-imgstorage",
                "Key.$": "States.Format('aiimg/{}/newsapi_log.json', $event_id)"
              },
              "Resource": "arn:aws:states:::aws-sdk:s3:putObject",
              "End": true
            }
          }
        }
      ],
      "ResultPath": "$.parallelResults",
      "Next": "Wait_to_publish"
    },
    "Wait_to_publish": {
      "Type": "Wait",
      "Seconds": 100,
      "Next": "Publishing"
    },
    "Publishing": {
      "Type": "Parallel",
      "Next": "GetObject",
      "Branches": [
        {
          "StartAt": "Creating Web content",
          "States": {
            "Creating Web content": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": "arn:aws:lambda:${ region }:${ accountid }:function:newsaiimg-${ environment }-webpagedesign-lambda-function:$LATEST"
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
              "Next": "CodeBuild StartBuild"
            },
            "CodeBuild StartBuild": {
              "Type": "Task",
              "Resource": "arn:aws:states:::codebuild:startBuild",
              "Parameters": {
                "ProjectName": "newsaiimg-${ environment }-codebuild-build-website"
              },
              "End": true
            }
          }
        }
      ]
    },
    "GetObject": {
      "Type": "Task",
      "Parameters": {
        "Bucket": "newsaiimg-${ environment }-s3-imgstorage",
        "Key.$": "States.Format('aiimg/{}/main.json', $event_id)"
      },
      "Resource": "arn:aws:states:::aws-sdk:s3:getObject",
      "Next": "SNS Publish"
    },
    "SNS Publish": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "Subject": "NEWSAI - New story",
        "Message.$": "$",
        "TopicArn": "arn:aws:sns:${ region }:${ accountid }:newsaiimg-${ environment }-sns-topic",
        "MessageAttributes": {
          "eventType": {
            "DataType": "String",
            "StringValue": "ALERT"
          },
          "incidentKey": {
            "DataType": "String",
            "StringValue.$": "$event_id"
          },
          "priority": {
            "DataType": "String",
            "StringValue": "LOW"
          },
          "incidentUrl1": {
            "DataType": "String",
            "StringValue.$": "States.Format('https://d305zk4rld5lm5.cloudfront.net/post/{}', $event_id)"
          }
        }
      },
      "End": true,
      "InputPath": "$.Body"
    }
  }
}