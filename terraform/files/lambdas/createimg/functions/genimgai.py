"""Useing AI to generate an imahe"""

import base64
import json
import logging
import random
import time

import boto3
import requests
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

    def gen_img_promt(self, news_story):
        """Function to score the story for picking"""
        pik_models = [
            {"provider": "meta", "id": "meta.llama3-8b-instruct-v1:0"},
            # {"provider": "aws", "id": "amazon.titan-text-express-v1"}
        ]
        img_styls = [
            "realistic",
            "artistic",
            "cartoon",
            "fantasy",
            "abstract",
            "anime",
            "manga",
            "cyberpunk",
            "retro",
            "vaporwave",
            "Hentai",
        ]
        img_style = random.choice(img_styls)
        logging.info("Image style picked: %s", img_style)
        prompt_text = f"""
        Task:
            Create an image prompt based on the following news story. The image should be visually appealing and relevant to the content of the story.
            The prompt should be suitable for an AI image generation model and should not contain any explicit or inappropriate content.
        Rules to follow:
            - The MAXIUM number of characters for the prompt is 400 it MUST not go any higher.
            - Include the image style of {img_style} in the prompt.
            - The description should be engaging, imaginative, and detailed.
            - Just inclde the promt for the image, DO NOT include any other text.
        This is the news Story:
        <story>{news_story}</story>
        """
        for pik_model in pik_models:
            logging.info("Stating AI on module %s", pik_model.get("id"))
            ai_reslt = ""
            if pik_model.get("provider") == "meta":
                ai_reslt = self.__invoke_meta_text_model__(
                    model_id=pik_model.get("id"), prompt=prompt_text
                )
            elif pik_model.get("provider") == "aws":
                ai_reslt = self.__invoke_aws_text_model__(
                    model_id=pik_model.get("id"), prompt=prompt_text
                )

            if ai_reslt is not None:
                if "\n" in ai_reslt:
                    logging.info(
                        "Found possable new line in so spliting %s", pik_model.get("id")
                    )
                    ai_reslt = ai_reslt.replace("\n", "")

                if ":" in ai_reslt:
                    logging.info(
                        "Found possable : in so spliting %s", pik_model.get("id")
                    )
                    logging.debug("Orginal: %s", ai_reslt)
                    ai_reslt = ":".join(ai_reslt.split(":")[1:])
                    logging.debug("Altred: %s", ai_reslt)

                if ai_reslt.startswith('"') and ai_reslt.endswith('"'):
                    logging.info(
                        "AI result starts and ends with quotes: %s", pik_model.get("id")
                    )
                    ai_reslt = ai_reslt[1:-1]
            else:
                logging.error("AI %s returned None", pik_model.get("id"))
                ai_reslt = None
        return {"model_id": pik_model.get("id"), "response": ai_reslt}

    def gen_aws_image(self, prompt):
        """Generate an image from the prompt"""
        model_id = "amazon.titan-image-generator-v1"
        native_request = json.dumps(
            {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {"text": prompt},
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 1024,
                    "width": 1024,
                    "cfgScale": 8.0,
                    "seed": 0,
                },
            }
        )
        accept = "application/json"
        content_type = "application/json"
        try:
            if not isinstance(prompt, str):
                raise ValueError("Prompt is not a string")
            promt_count = len(prompt)
            logging.info("Prompt count is: %s", promt_count)
            if promt_count >= 512:
                raise ValueError("Prompt is longer than 512 characters")
            response = self.bedrockclient.invoke_model(
                body=native_request,
                modelId=model_id,
                accept=accept,
                contentType=content_type,
            )
            response_body = json.loads(response.get("body").read())
            base64_image = response_body.get("images")[0]
            base64_bytes = base64_image.encode("ascii")
            image_bytes = base64.b64decode(base64_bytes)
            return {
                "image_data": image_bytes,
                "AI": {
                    "model_id": model_id,
                    "prompt": prompt,
                },
            }
        except (ClientError, ValueError) as aierr:  # pylint: disable=W0718
            logging.error("Can't invoke %s Reason: %s", model_id, aierr)
            return {
                "error_type": str(aierr.__class__.__name__),
                "error_msg": str(aierr),
                "image_data": None,
                "AI": {
                    "model_id": model_id,
                    "prompt": prompt,
                },
            }

    # None main ones
    def __invoke_aws_text_model__(
        self, model_id="amazon.titan-text-express-v1", prompt=""
    ):
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
        try:
            request = json.dumps(native_request)
            response = self.bedrockclient.invoke_model(modelId=model_id, body=request)
            model_response = json.loads(response["body"].read())
            results = model_response["results"][0]["outputText"]
        except ClientError as invokeerr:
            if invokeerr.response["Error"]["Code"] == "ThrottlingException":
                logging.error("model id: %s ThrottlingException", model_id)
                results = None
                time.sleep(10)
            else:
                logging.error("model id: %s Error found: %s", model_id, invokeerr)
                results = None
        except ValueError as invokeerr:
            logging.error("model id: %s ValueError: %s", model_id, invokeerr)
            results = None
        return results

    def __invoke_meta_text_model__(
        self, model_id="meta.llama3-8b-instruct-v1:0", prompt=""
    ):
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
            results = model_response["generation"]
        except ClientError as invokeerr:
            if invokeerr.response["Error"]["Code"] == "ThrottlingException":
                logging.error("model id: %s ThrottlingException", model_id)
                time.sleep(10)
                results = None
            else:
                results = None
        except ValueError as invokeerr:
            logging.error("model id: %s ValueError: %s", model_id, invokeerr)
            results = None
        return results


class OPENai:
    """Class for all need openai AI stuff"""

    def __init__(self, apitoken=None, apiproject=None, apiorg=None):
        self.apiproject = apiproject
        self.headers = {
            "Authorization": f"Bearer {apitoken}",
            "OpenAI-Organization": apiorg,
            "OpenAI-Project": apiproject,
        }

    def list_models(self):
        """List all modules for openai"""
        url = "https://api.openai.com/v1/models"
        response = requests.get(url, headers=self.headers, timeout=20)
        if response.status_code == 200:
            mlist = response.json()
        else:
            logging.error("Error %s", {response.text})
            mlist = None
        return mlist

    # need to add image gen
    def gen_image(self, prompt=None, model_id="dall-e-3"):
        """Generate an image use OPENAI"""
        results = {
            "image_data": "",
            "AI": {
                "model_id": f"openai_{model_id}",
                "prompt": prompt,
            },
        }

        logging.info("Promt size: %s", len(prompt))
        try:
            url = "https://api.openai.com/v1/images/generations"
            data = {
                "model": model_id,
                "prompt": prompt,
                "n": 1,  # number of images to generate
                "size": "1024x1024",  # other options: 256x256, 512x512 for DALL-E 2
            }
            response = requests.post(url, headers=self.headers, json=data, timeout=300)
            # Check the result
            if response.status_code == 200:
                results["img_path"] = response.json()["data"][0]["url"]
                logging.debug("Image path: %s", results["img_path"])
                # Retrieve the image URL and fetch the image data
                image_url = response.json()["data"][0]["url"]
                image_response = requests.get(image_url, timeout=300)
                results["image_data"] = image_response.content
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except ValueError as invokeerr:
            logging.error("model id: %s ValueError: %s", model_id, invokeerr)
            results["error_type"] = str(invokeerr.__class__.__name__)
            results["error_msg"] = str(invokeerr)
        return results

    # need to add  text gen
