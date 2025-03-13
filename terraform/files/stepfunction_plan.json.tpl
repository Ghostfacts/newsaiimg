{
  "Comment": "A Hello World example of the Amazon States Language using a Pass state",
  "StartAt": "GetNewsStories",
  "States": {
    "GetNewsStories": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "OutputPath": "$.Payload",
      "Parameters": {
        "Payload.$": "$",
        "FunctionName": "${newapi_lmb_function}"
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
      "Next": "Map"
    },
    "Map": {
      "Type": "Map",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "INLINE",
        },
        "StartAt": "Bedrock InvokeModel",
        "States": {
          "Bedrock InvokeModel": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Parameters": {
              "ModelId": "arn:aws:bedrock:eu-west-2::foundation-model/amazon.titan-text-lite-v1",
              "Body": {
                "inputText": "help me understand bedrok",
                "textGenerationConfig": {
                  "temperature": 0,
                  "topP": 1,
                  "maxTokenCount": 512
                }
              }
            },
            "End": true
          }
        }
      },
      "End": true,
      "Label": "Map",
      "MaxConcurrency": 1000
    }
  }
}