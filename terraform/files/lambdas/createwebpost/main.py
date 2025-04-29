"""Code to create webpage content"""

import json
import logging
import os
from io import BytesIO

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from PIL import Image

# from datetime import datetime, timezone


if len(logging.getLogger().handlers) > 0:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


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


# main code
def lambda_handler(event, context):  # pylint: disable=W0613,R1710
    """Main lambda handler Where it all starts"""
    # Defult Return info
    result = {
        "statusCode": 200,
        "body": json.dumps("Hello from Lambda!"),
    }

    try:
        # Returns the ssm prmater for all info
        ssm_client = boto3.client("ssm", region_name=os.getenv("region") or "eu-west-2")
        ssm_data = json.loads(
            ssm_client.get_parameter(
                Name=os.getenv("SSM_PARAMETER_NAME") or "/newsaiimg/dev/lambdasettings",
                WithDecryption=True,
            )["Parameter"]["Value"]
        )
        s3_client = boto3.client("s3")
        logging.info(
            "Getting josn data: %s",
            f"s3://{ssm_data["ais3bucket"]}/aiimg/{event.get('event_id')}/main.json",
        )
        json_data = json.loads(
            s3_client.get_object(
                Bucket=ssm_data["ais3bucket"],
                Key=f"aiimg/{event.get('event_id')}/main.json",
            )["Body"]
            .read()
            .decode("utf-8")
        )
        logging.info(
            "Getting image data: %s",
            f"s3://{ssm_data["ais3bucket"]}/aiimg/{event.get('event_id')}/newsimage.png",
        )
        news_image = Image.open(
            BytesIO(
                s3_client.get_object(
                    Bucket=ssm_data["ais3bucket"],
                    Key=f"aiimg/{event.get('event_id')}/newsimage.png",
                )["Body"].read()
            )
        )

        logging.info(
            "Resize image (website) and uploading, path %s",
            f"s3://{ssm_data["sites3bucket"]}/website/content/images/{json_data.get('eventid')}/main.jpg",
        )
        webimg = resize_image(news_image, width=500)
        with BytesIO() as output:
            webimg.save(output, format="JPEG")
            s3_client.put_object(
                Bucket=ssm_data["sites3bucket"],
                Key=f"website/content/images/{json_data.get('eventid')}/main.jpg",
                Body=output.getvalue(),
            )
        logging.info(
            "Resize image (thumnail) and uploading, path %s",
            f"s3://{ssm_data["sites3bucket"]}/website/content/images/{json_data.get('eventid')}/main.jpg",
        )
        webimg = resize_image(news_image, width=70)
        with BytesIO() as output:
            webimg.save(output, format="JPEG")
            s3_client.put_object(
                Bucket=ssm_data["sites3bucket"],
                Key=f"website/content/images/{json_data.get('eventid')}/thum.jpg",
                Body=output.getvalue(),
            )
        logging.info("AI the story info")

        logging.info(
            "Create Markdown file and upload to s3 path: %s",
            f"s3://{ssm_data["sites3bucket"]}/website/content/post/{json_data.get('eventid')}.md",
        )

        # print(
        #     json.dumps(
        #         json_data,
        #         indent=4,
        #     )
        # )

    # Error handeling
    except EndpointConnectionError as e:
        logging.error("Endpoint connection error: %s", str(e))
        result["statusCode"] = 500
        result["error"] = json.dumps({"error": "Endpoint connection error"})
    except ClientError as e:
        logging.error("Client error: %s", str(e))
        result["statusCode"] = 500
        result["error"] = json.dumps({"error": "Client error"})

    # Return the result
    return result
