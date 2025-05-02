"""Useing AI to score news storys"""

import json
import logging
import time

import boto3
from botocore.exceptions import ClientError


class AWSai:
    """Class for all need AWS AI stuff"""

    def __init__(self, region="eu-west-1"):
        """Initializes the AWS Bedrock client."""
        self.region = region
        self.bedrockclient = boto3.client("bedrock-runtime", region_name=self.region)

    def list_models(self):
        """Lists available foundation models in AWS Bedrock."""
        try:
            models = []
            bedrock_client = boto3.client("bedrock", region_name=self.region)
            response = bedrock_client.list_foundation_models()
            for model in response.get("modelSummaries"):
                models.append(
                    {
                        "name": model.get("modelName"),
                        "arn": model.get("modelArn"),
                        "inputModalities": model.get("inputModalities"),
                        "outputModalities": model.get("outputModalities"),
                        "providerName": model.get("providerName"),
                        "modelLifecycle": model.get("modelLifecycle"),
                    }
                )
            return models
        except (ClientError, Exception) as e:  # pylint: disable=W0718
            logging.error("Error listing models: %s", str(e))
            return []

    def alter_story(self, news_story):
        """Alter Story to fix web site"""
        pik_models = [
            {"provider": "meta", "id": "meta.llama3-8b-instruct-v1:0"},
            {"provider": "aws", "id": "amazon.titan-text-express-v1"},
            {"provider": "aws", "id": "amazon.titan-text-lite-v1"},
        ]
        prompt_text = f"""
        Your tasks completed in this order:
        - Take the news story and write an short version of the story for the web site
            - It should only be an few lines maxium for 10 lines
            - It needs to be relevent to th story
            - Make it easy to read like for a 7 year old to understand

        Here is the news story to score:
        \"\"\"{news_story}\"\"\"
        """
        ai_score_reslt = ""
        for pik_model in pik_models:
            if pik_model.get("provider") == "meta":
                ai_score_reslt = self.__invoke_meta_model__(
                    model_id=pik_model.get("id"), prompt=prompt_text
                )
            elif pik_model.get("provider") == "aws":
                ai_score_reslt = self.__invoke_aws_model__(
                    model_id=pik_model.get("id"), prompt=prompt_text
                )
            ai_score_reslt["model_id"] = pik_model.get("id")
            if ai_score_reslt.get("result", "fail") == "passed":
                break
        return ai_score_reslt

    # None main ones
    def __invoke_aws_model__(self, model_id="amazon.titan-text-express-v1", prompt=""):
        """
        Invokes the specified model with the supplied prompt.
        :param model_id: The model ID for the model that you want to use.
        :param prompt: The prompt that you want to send to the model.

        :return: The text response from the model.
        """
        logging.debug("Triggering LLM %s", model_id)
        native_request = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 1000,
                "temperature": 0.1,
                "topP": 0.1,
            },
        }
        request = json.dumps(native_request)
        try:
            response = self.bedrockclient.invoke_model(modelId=model_id, body=request)
            model_response = json.loads(response["body"].read())
            results = {
                "result": "passed",
                "body": model_response["results"][0]["outputText"],
            }
            logging.debug("Raw AI %s output: %s", model_id, results)
        except ClientError as invokeerr:
            if invokeerr.response["Error"]["Code"] == "ThrottlingException":
                logging.error("model id: %s ThrottlingException", model_id)
                results = {
                    "result": "fail",
                    "body": "ThrottlingException",
                }
                time.sleep(10)
            else:
                logging.error("model id: %s Error found: %s", model_id, invokeerr)
                results = {
                    "result": "fail",
                    "body": "Unknown error, check logs",
                }
        except ValueError as invokeerr:
            logging.error("model id: %s ValueError: %s", model_id, invokeerr)
            results = {"result": "fail", "body": "ValueError Found"}
        return results

    def __invoke_meta_model__(self, model_id="meta.llama3-8b-instruct-v1:0", prompt=""):
        """This is to call on a Meta type Bedrock AI"""
        formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>user<|end_header_id|>
        {prompt}
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
        logging.debug("Triggering LLM %s", model_id)
        native_request = {
            "prompt": formatted_prompt,
            "max_gen_len": 1000,
            "temperature": 0.1,
        }
        request = json.dumps(native_request)
        try:
            response = self.bedrockclient.invoke_model(modelId=model_id, body=request)
            model_response = json.loads(response["body"].read())
            results = {
                "result": "passed",
                "body": json.loads(model_response["generation"]),
            }
            logging.debug("Raw AI %s output: %s", model_id, results)
        except ClientError as invokeerr:
            if invokeerr.response["Error"]["Code"] == "ThrottlingException":
                logging.error("model id: %s ThrottlingException", model_id)
                time.sleep(10)
                results = {
                    "result": "fail",
                    "score": "0",
                    "reason": "ThrottlingException",
                }
            else:
                results = {
                    "result": "fail",
                    "score": "0",
                    "reason": "Unknown error, check logs",
                }
        except ValueError as invokeerr:
            logging.error("model id: %s ValueError: %s", model_id, invokeerr)
            results = {"result": "fail", "score": "0", "reason": "ValueError Found"}
        return results
