"""Genai funtions for newsAI"""

import json
import logging
import time

import boto3
from botocore.exceptions import ClientError


class Bedrock:
    """Class bock for genAI"""

    def __init__(self, region="eu-west-1"):
        """Initializes the AWS Bedrock client."""

        self.region = region
        self.bedrockclient = boto3.client("bedrock-runtime", region_name=self.region)

    def list_models(self):
        """Lists available foundation models in AWS Bedrock."""
        try:
            bedrock_client = boto3.client("bedrock", region_name=self.region)
            response = bedrock_client.list_foundation_models()
            models = [model["modelId"] for model in response.get("modelSummaries", [])]
            return models
        except (ClientError, Exception) as e:  # pylint: disable=W0718
            print(f"Error listing models: {str(e)}")
            return []

    def __invoke_model__(self, model_id="amazon.titan-text-express-v1", prompt=""):
        """
        Invokes the specified model with the supplied prompt.
        :param model_id: The model ID for the model that you want to use.
        :param prompt: The prompt that you want to send to the model.

        :return: The text response from the model.
        """

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
            return {
                "model_id": model_id,
                "outputText": model_response["results"][0]["outputText"],
            }
        except (ClientError, Exception) as e:  # pylint: disable=W0718
            logging.error("Can't invoke %s Reason: %s", model_id, e)
            return None  # Return None instead of raising an error

    def news_reviews(self, news_story):
        """
        This function processes a news story using an LLM and extracts:
        :param news_story: The news story text
        :return: Processed summary from the model
        """
        news_reviews = []
        ia_model_ids = [
            "amazon.titan-text-express-v1",
            "amazon.titan-text-lite-v1",
        ]
        prompt_text = f"""
        Your tasks completed in this order:
        - Audit the story and provied it an score from 0 to 20 base the score on the fallowing needs
            - The Story need to be happy
            - The Story can not be about war
            - The Story can not be goverment
            - The Story can not be about drugs
            - The Story can not be about crime
        - Your respone MUST be formated in the fallowing way
            - MUST meet the requirments to be an be a valid JSON object
            - With an key value called 'result' its value is if the story is an pass or fail
            - With an key value called 'score': the score you gave the story
            - With an key value called 'reson': the reson why you gave the story that score

        Here is the news story to score:
        \"\"\"{news_story}\"\"\"
        """
        try:
            for ia_model_id in ia_model_ids:
                airesponce = self.__invoke_model__(
                    prompt=prompt_text, model_id=ia_model_id
                )
                # data clean up
                news_reviews.append(
                    {
                        "model_id": airesponce["model_id"],
                        "results": json.loads(airesponce["outputText"]),
                    }
                )
                time.sleep(5)
        except Exception as e:  # pylint: disable=W0718
            logging.error("Error processing news story: %s", str(e))
            logging.info("AI output: %s", airesponce)
        return news_reviews
