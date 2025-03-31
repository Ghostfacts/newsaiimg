"""Generate Image from Story"""

import os
import tempfile

import genai


# main
def lambda_handler(event, context):  # pylint: disable=W0613
    """defult Lambda function"""
    temp_dir = (
        tempfile.TemporaryDirectory()  # pylint: disable=R1732 #dont want to use an with
    )
    log_id = getattr(context, "log_stream_name", None)
    newsai = genai.Genai(region="eu-west-2")
    # Create a temporary folder in /tmp/
    promt = newsai.generate_image(
        story=event["story"], imagepath=os.path.join(temp_dir.name)
    )
    # send files to s3
    # image
    # promt
    temp_dir.cleanup()
    return {
        "statusCode": promt.get("status_code"),
        "image_path": promt.get("imgpath"),
        "ai_data": {
            "prompt": promt.get("prompt"),
            "model_id": promt.get("model_id"),
        },
        "error": promt.get("error"),
        "log_id": log_id,
    }
