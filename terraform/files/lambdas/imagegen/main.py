"""Generate Image from Story"""

import json
import logging
import os
import tempfile

import boto3
import genai


def upload_to_s3(file_path, bucket_name, s3_key):
    """Upload a file to an S3 bucket"""
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(file_path, bucket_name, s3_key)
        logging.info("Uploading %s to s3://%s/%s", file_path, bucket_name, s3_key)
    except Exception as e:
        logging.error("Failed to upload %s to S3: %s", file_path, e)
        raise


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
    temp_dir = (
        tempfile.TemporaryDirectory()  # pylint: disable=R1732 #dont want to use an with
    )
    log_id = getattr(context, "log_stream_name", None)
    newsai = genai.Genai(region=ssm_data["region"])
    # Create a temporary folder in /tmp/
    promt = newsai.generate_image(
        story=event["story"], imagepath=os.path.join(temp_dir.name)
    )
    # Write a JSON file to the temporary folder
    json_data = {
        "event_id": event.get("event_id"),
        "ai_data": {
            "prompt": promt.get("prompt"),
            "model_id": promt.get("model_id"),
        },
    }
    json_file_path = os.path.join(temp_dir.name, "gen_image_data.json")
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file)
    bucket_name = ssm_data["ais3bucket"]
    for file_name in os.listdir(temp_dir.name):
        file_path = os.path.join(temp_dir.name, file_name)
        s3_key = f"{event.get('event_id')}/{file_name}"
        upload_to_s3(file_path, bucket_name, s3_key)
    temp_dir.cleanup()
    return {
        "statusCode": promt.get("status_code"),
        "image_path": f"s3://{ssm_data['ais3bucket']}/{event.get('event_id')}/newsimage.png",
        "ai_data": {
            "prompt": promt.get("prompt"),
            "model_id": promt.get("model_id"),
        },
        "error": promt.get("error"),
        "log_id": log_id,
    }
