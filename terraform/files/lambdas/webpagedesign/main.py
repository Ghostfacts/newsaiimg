"""Created the needed content to display the image"""

import json
import logging
import os
from datetime import datetime, timezone
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def resize_image(image, width=None, size=None):
    """Resize the image"""
    img_resiz = image
    if width:
        w_percent = width / float(image.size[0])
        h_size = int((float(image.size[1]) * float(w_percent)))
        img_resiz = image.resize(
            (width, h_size), Image.LANCZOS  # pylint: disable=E1101
        )
    elif size:
        img_resiz = image.resize(size, Image.LANCZOS)  # pylint: disable=E1101
    return img_resiz


def image_to_bytes(image):
    """Convert PIL Image to bytes"""
    with BytesIO() as output:
        image.save(output, format="JPEG")
        return output.getvalue()


s3_client = boto3.client("s3")


def s3_write_file(bucketname, key, data):
    """Write s3 file"""
    try:
        logger.debug("Writing to S3 bucket: %s, key: %s", bucketname, key)
        s3_client.put_object(Bucket=bucketname, Key=key, Body=data)
        logger.info("Successfully wrote to S3 bucket: %s, key: %s", bucketname, key)
    except (BotoCoreError, ClientError) as error:  # Handle specific exceptions
        logger.error("S3 Write error: %s", str(error))


def s3_read_file(bucketname, key):
    """Read an s3 file"""
    try:
        logger.debug("Reading from S3 bucket: %s, key: %s", bucketname, key)
        response = s3_client.get_object(Bucket=bucketname, Key=key)
        logger.info("Successfully read from S3 bucket: %s, key: %s", bucketname, key)
        return response["Body"].read()
    except (BotoCoreError, ClientError) as error:  # Handle specific exceptions
        logger.error("S3 Read error: %s", str(error))
        return None  # Return None if reading fails


# main
def lambda_handler(event, context):  # pylint: disable=unused-argument
    """Default Lambda function"""
    try:
        logger.info("Lambda handler invoked with event: %s", event)
        # Retrieve JSON object from SSM Parameter Store
        logger.debug("Fetching SSM parameter")
        ssm_client = boto3.client("ssm", region_name="eu-west-2")
        ssm_parameter_name = os.getenv("SSM_PARAMETER_NAME", "/newsaiimg/dev/settings")
        ssm_data = json.loads(
            ssm_client.get_parameter(
                Name=ssm_parameter_name,
                WithDecryption=True,
            )[
                "Parameter"
            ]["Value"]
        )
        logger.info("Successfully fetched SSM parameter")

        logger.debug("Reading JSON data from S3")
        json_data = json.loads(
            s3_read_file(
                bucketname=ssm_data["ais3bucket"],
                key=f"aiimg/{event.get('event_id')}/main.json",
            ).decode("utf-8")
        )
        if not json_data:
            logger.error("Failed to read JSON data from S3")
            return {
                "status": 500,
                "LogStreamName": getattr(context, "log_stream_name", None),
            }

        logger.debug("Reading image data from S3")
        imagedata = s3_read_file(
            bucketname=ssm_data["ais3bucket"],
            key=f"aiimg/{json_data.get('eventid')}/main.png",
        )
        if not imagedata:
            logger.error("Failed to read image data from S3")
            return {
                "status": 500,
                "LogStreamName": getattr(context, "log_stream_name", None),
            }

        logger.debug("Resizing images")
        image = Image.open(BytesIO(imagedata))
        thumbnail = resize_image(image, width=70)
        webimage = resize_image(image, width=500)
        logger.info("Successfully resized images")
        # Want to look at adding an water mark to the main image
        logger.debug("Converting images to bytes")
        thumbnail_bytes = image_to_bytes(thumbnail)
        webimage_bytes = image_to_bytes(webimage)

        logger.debug("Writing resized images to S3")
        s3_write_file(
            bucketname=ssm_data["ais3bucket"],
            key=f"website/content/images/{json_data.get('eventid')}/thum.jpg",
            data=thumbnail_bytes,
        )
        s3_write_file(
            bucketname=ssm_data["ais3bucket"],
            key=f"website/content/images/{json_data.get('eventid')}/main.jpg",
            data=webimage_bytes,
        )
        logger.info("Successfully wrote resized images to S3")

        logger.debug("Writing markdown file to S3")
        pagejson = {
            "title": json_data["picked_article"]["title"].replace("'", ""),
            "id": json_data.get("eventid"),
        }
        #  will need to workout wau to add more latters 
        site_keywords = "AI-test"
        page = f"""
+++
title = '{pagejson["title"]}'
id ='{pagejson["id"]}'
date = {datetime.now(timezone.utc).astimezone().isoformat()}
draft = false
Keywords = '{site_keywords}'
Cover   = 'images/{json_data.get('eventid')}/main.jpg'
+++

### About the Story
- Story Source: [{json_data['picked_article'].get('source', 'Website')}]({json_data['picked_article']['url']})
- Story Author: {json_data['picked_article'].get('author', '')}

{json_data['picked_article']['description']}

### Promnt used for the image
{json_data["genimage"]['prompt']}

### AI moduled used
{json_data["genimage"]['model_id']}
        """
        s3_write_file(
            bucketname=ssm_data["ais3bucket"],
            key=f"website/content/post/{json_data.get('eventid')}.md",
            data=page,
        )

        logger.info("Successfully wrote markdown file to S3")

        return {
            "status": 200,
            "LogStreamName": getattr(context, "log_stream_name", None),
        }
    except (BotoCoreError, ClientError, json.JSONDecodeError, KeyError) as error:
        logger.error("Error occurred: %s", str(error))
        return {
            "status": 500,
            "LogStreamName": getattr(context, "log_stream_name", None),
            "Error": str(error),
        }
