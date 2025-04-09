"""Genai funtions for newsAI"""

import base64
import io
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from PIL import Image


class Genai:  # pylint: disable=R0903
    """All required genai commands needed for the newsAI"""

    def __init__(self, region="eu-west-2"):
        """Initializes the AWS Bedrock client."""
        self.region = region
        self.bedrockclient = boto3.client("bedrock-runtime", region_name=self.region)

    def generate_image(self, story, imagepath):
        """Generate an image from the story"""
        story_prompt = self.__image_promt(story)
        imgestyle = "realistic"
        image_promt = f"""
        Task:
            Make an {imgestyle} photo based on: {story_prompt.get("outputText")}
        """
        image_promt = " ".join(image_promt.split())
        # Remove any new lines (\n) from the image prompt
        image_promt = image_promt.replace("\n", " ")
        # Ensure the image prompt does not exceed 512 characters
        if len(image_promt) > 512:
            logging.warning(
                "Over max caracters, truncating to 510 from %s", len(image_promt)
            )
            image_promt = image_promt[:510]
        else:
            logging.info("Image prompt length: %s characters", len(image_promt))

        word_count = len(image_promt.split())
        logging.info("Image prompt word count: %s words", word_count)

        # The image prompt is the output of the text generation model
        image_bytes = self.__gen_image(image_promt)
        result = {
            "status_code": 200,
            "imgpath": os.path.join(imagepath, "newsimage.png"),
            "model_id": story_prompt.get("model_id"),
            "prompt": image_promt,
        }
        if image_bytes is None:
            logging.error("No image data returned")
        else:
            logging.info("Image data returned")
            image = Image.open(io.BytesIO(image_bytes["image_data"]))
            image = image.convert("RGB")
            image.save(os.path.join(imagepath, "newsimage.png"), "PNG")
            image.close()
        return result

    def __gen_image(self, prompt):
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
        except (ClientError, Exception) as e:  # pylint: disable=W0718
            # logging.error("Can't invoke %s Reason: %s", model_id, e)
            logging.error("Can't invoke %s Reason: %s", model_id, e)
            return None

    def __image_promt(self, story):
        """Create an prompt for the image generation"""
        if "source" in story:
            del story["source"]
        if "author" in story:
            del story["author"]
        # model_id="amazon.titan-text-lite-v1"
        model_id = "amazon.titan-text-express-v1"
        prompt_text = f"""  # pylint: disable=R0903
        Task:
            Generate a creative and visually descriptive prompt to,
            create an AI-generated image based on the news story provided.
        Rules to follow:
            - The prompt must fully comply with AWS Responsible AI Policies and Acceptable Use Policies.
            - The content must be appropriate for all ages (no explicit, violent, hateful, or mature themes).
            - Avoid political, religious, or culturally sensitive topics that may be controversial or divisive.
            - Do not reference real people, trademarks, or copyrighted characters directly.
            - The generated prompt must not include any misleading or false information.
            - The prompt must be between 300 and 400 characters long (including spaces).
            - The description should be engaging, imaginative, and detailed.
            - Just inclde the promt for the image, do not include any other text.
        This is the news Story:
        <story>{story}</story>
        """
        native_request = {
            "inputText": prompt_text,
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
            raise Exception("Invoke of model failed") from e  # pylint: disable=W0719
