import boto3
import json
import logging
from botocore.exceptions import ClientError

class Bedrock:
    def __init__(self, region="eu-west-1"):
        """
        Initializes the AWS Bedrock client.
        :param region: AWS region where Bedrock is available.
        """
        self.region = region
        self.bedrockclient = boto3.client("bedrock-runtime", region_name=self.region)

    def list_models(self):
        """
        Lists available foundation models in AWS Bedrock.
        """
        try:
            bedrock_client = boto3.client("bedrock", region_name=self.region)
            response = bedrock_client.list_foundation_models()
            models = [model["modelId"] for model in response.get("modelSummaries", [])]
            return models
        except Exception as e:
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
                "topP": 0.1
            }
        }

        request = json.dumps(native_request)

        try:
            response = self.bedrockclient.invoke_model(modelId=model_id, body=request)
            model_response = json.loads(response["body"].read())
            return {
                "model_id": model_id,
                "outputText": model_response["results"][0]['outputText']
            }

        except (ClientError, Exception) as e:
            print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
            return None  # Return None instead of raising an error

    def news_reviews(self, news_story):
        """
        This function processes a news story using an LLM and extracts:
        :param news_story: The news story text
        :return: Processed summary from the model
        """
        news_reviews=[]
        ia_model_ids =[
            "amazon.titan-text-express-v1",
            "amazon.titan-text-lite-v1",
        ]
        prompt_text = f"""
        Your tasks completed in this order:
        - Audit the story and provied it an score from 0 to 20 please base the score on the fallowing needs
         - The Story need to be happy
         - The Story can not be about war
         - The Story can not be goverment
        - Your respone MUST be formated in the fallowing way
          - MUST be a valid JSON object
          - With an key value called 'result' its value is if the story is an pass or fail
          - With an key value called 'score': the score you gave the story
          - With an key value called 'reson': the reson why you gave the story that score


        Here is the news story to score:
        \"\"\"{news_story}\"\"\"
        """


        for ia_model_id in ia_model_ids:
            info = self.__invoke_model__(
                prompt=prompt_text,
                model_id=ia_model_id
            )
            news_reviews.append({
                "model_id": info['model_id'],
                "results": json.loads(info['outputText'])
            })
        return news_reviews