"""Generate Image from Story"""

import json
import logging
import os
import tempfile

import boto3
from functions import genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

s3_client = boto3.client("s3")


def s3_write_file(bucketname, key, data):
    """Write s3 file"""
    try:
        s3_client.put_object(Bucket=bucketname, Key=key, Body=data)
    except Exception as e:  # pylint: disable=W0718
        logging.error("S3 Write error: %s", str(e))


def s3_read_file(bucketname, key):
    """Read an se file"""
    try:
        response = s3_client.get_object(Bucket=bucketname, Key=key)
        return str(response["Body"].read().decode("utf-8"))
    except Exception as e:  # pylint: disable=W0718
        logging.error("S3 Read error: %s", str(e))
        return None


# main
def lambda_handler(event, context):  # pylint: disable=W0613
    """defult Lambda function"""
    # Retrieve JSON object from SSM Parameter Store
    ssm_client = boto3.client("ssm", region_name="eu-west-2")
    ssm_data = json.loads(
        ssm_client.get_parameter(
            Name=os.getenv("SSM_PARAMETER_NAME") or "/newsaiimg/dev/settings",
            WithDecryption=True,
        )["Parameter"]["Value"]
    )
    log_id = getattr(context, "log_stream_name", None)
    newsai = genai.Genai(region=ssm_data["region"])
    json_data = json.loads(
        s3_read_file(
            bucketname=ssm_data["ais3bucket"],
            key=f"aiimg/{event.get('event_id')}/main.json",
        )
    )

    temp_dir = (
        tempfile.TemporaryDirectory()  # pylint: disable=R1732 #dont want to use an with
    )
    promt = newsai.generate_image(
        story=json_data["picked_article"], imagepath=os.path.join(temp_dir.name)
    )
    # Read the generated image from promt['imgpath']
    try:
        with open(promt["imgpath"], "rb") as image_file:
            image_data = image_file.read()
        # Write the image data to the S3 bucket
        s3_write_file(
            bucketname=ssm_data["ais3bucket"],
            key=f"aiimg/{event.get('event_id')}/main.png",
            data=image_data,
        )
    except Exception as e:  # pylint: disable=W0718
        logging.error("Error reading or writing image: %s", str(e))

    json_data["genimage"] = {
        "prompt": promt.get("prompt"),
        "model_id": promt.get("model_id"),
        "imagepath": f"s3://{ssm_data["ais3bucket"]}/aiimg/{event.get('event_id')}/main.png",
    }
    s3_write_file(
        bucketname=ssm_data["ais3bucket"],
        key=f"aiimg/{event.get("event_id")}/main.json",
        data=json.dumps(json_data, indent=2).encode("utf-8"),
    )
    temp_dir.cleanup()
    return {
        "statusCode": promt.get("status_code"),
        "image_path": f"s3://{ssm_data["ais3bucket"]}/aiimg/{event.get('event_id')}/main.png",
        "ai_data": json_data["genimage"],
        "error": promt.get("error"),
        "log_id": log_id,
    }
