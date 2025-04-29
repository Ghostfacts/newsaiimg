"""Lambda function for taking sotrie and Creating an image"""

import io
import json
import logging
import os
import tempfile
import time

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from functions import genimgai  # pylint: disable=E0611
from PIL import Image

if len(logging.getLogger().handlers) > 0:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def save_img(img_data, img_path):
    """Function to save the image"""
    image = Image.open(io.BytesIO(img_data))
    image = image.convert("RGB")
    image.save(img_path, "PNG")
    image.close()


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
        json_data = json.loads(
            s3_client.get_object(
                Bucket=ssm_data["ais3bucket"],
                Key=f"aiimg/{event.get('event_id')}/main.json",
            )["Body"]
            .read()
            .decode("utf-8")
        )
        aws_imgsai = genimgai.AWSai(region=os.getenv("region") or "eu-west-2")
        open_imgsai = genimgai.OPENai(
            apitoken=ssm_data["openai_token"],
            apiproject=ssm_data["openai_project"],
            apiorg=ssm_data["openai_org"],
        )

        imggen = {"max": 5, "attempts": 0, "tmpdir": tempfile.mkdtemp()}

        while imggen.get("attempts") < imggen.get("max"):
            imgpath = os.path.join(imggen.get("tmpdir"), "newsimage.png")
            story_promt = aws_imgsai.gen_img_promt(
                json_data["picked_article"]["content"]
            )
            # Checks the AWS one first
            ai_image = aws_imgsai.gen_aws_image(prompt=story_promt["response"])
            if ai_image.get("error_type") is not None:
                logging.error(
                    "AI %s error: %s",
                    ai_image.get("AI").get("model_id"),
                    ai_image.get("error_msg"),
                )
                # if AWS iMG was not good then try different one as soon as i writen it in
            else:
                logging.info(
                    "AI %s image generated", ai_image.get("AI").get("model_id")
                )
                save_img(ai_image["image_data"], img_path=imgpath)
                break

            # Run the next AI image gen (?????)

            # Run the next AI image gen (openAI say)
            ai_image = open_imgsai.gen_image(
                prompt=story_promt["response"]
            )  # not creted yet
            if ai_image.get("error_type") is not None:
                logging.error(
                    "AI %s error: %s",
                    ai_image.get("model_id"),
                    ai_image.get("error_msg"),
                )
            else:
                save_img(ai_image["image_data"], img_path=imgpath)
                break

            # If both fail then wait and try again
            imggen["attempts"] += 1
            time.sleep(5)

        # If maxed then out then raise error
        if imggen.get("attempts") == imggen.get("max"):
            raise ValueError("Max retries reached for image generation")

        # Adding promt data in to josn data
        json_data["ai_img"] = {
            "promt": story_promt.get("response"),
            "promt_model": story_promt.get("model_id"),
            "img_model": ai_image.get("AI").get("model_id"),
        }
        logging.info("Save image: %s", imgpath)
        s3_client.upload_file(
            imgpath,
            ssm_data["ais3bucket"],
            f"aiimg/{event.get('event_id')}/newsimage.png",
            ExtraArgs={"ContentType": "image/png"},
        )
        logging.info("Image uploaded")
        logging.info(
            "image path: %s",
            f"s3://{ssm_data["ais3bucket"]}/aiimg/{event.get('event_id')}/newsimage.png",
        )
        # Upload the JSON data to S3
        s3_client.put_object(
            Bucket=ssm_data["ais3bucket"],
            Key=f"aiimg/{event.get('event_id')}/main.json",
            Body=json.dumps(json_data),
            ContentType="application/json",
        )
        logging.info("JSON data uploaded")
        logging.info(
            "JSON path: %s",
            f"s3://{ssm_data["ais3bucket"]}/aiimg/{event.get('event_id')}/main.json",
        )

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
