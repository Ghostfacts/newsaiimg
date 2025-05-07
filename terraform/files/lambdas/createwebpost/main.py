"""Code to create webpage content"""

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from io import BytesIO

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from functions import newsai
from PIL import Image

# from datetime import datetime, timezone


if len(logging.getLogger().handlers) > 0:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


editerai = newsai.AWSai(region="eu-west-2")


def resize_and_save_image(image, width=None, size=None, s3info=None):
    """Resize the image"""
    img_resiz = image
    if width:
        w_percent = width / float(image.size[0])
        h_size = int((float(image.size[1]) * float(w_percent)))
        img_resiz = image.resize(
            (width, h_size), Image.Resampling.LANCZOS  # pylint: disable=E1101
        )
    elif size:
        img_resiz = image.resize(
            size, Image.Resampling.LANCZOS
        )  # pylint: disable=E1101
    if s3info is None:
        logging.info("NO s3 returning image")
        return img_resiz
    s3_client = boto3.client("s3")
    with BytesIO() as output:
        img_resiz.save(output, format="JPEG")
        s3_client.put_object(
            Bucket=s3info["bucket"],
            Key=s3info["key"],
            Body=output.getvalue(),
        )
    return True


def watermark_image(imagedata):
    """Watermark the image with transparency and resizing"""
    # Open the watermark image
    watermark = Image.open("watermark.png").convert("RGBA")

    # Resize the watermark to 20% of the original image size
    watermark_width = int(imagedata.size[0] * 0.3)
    watermark_height = int(imagedata.size[1] * 0.3)
    watermark = watermark.resize(
        (watermark_width, watermark_height), Image.Resampling.LANCZOS
    )

    # Make the watermark 70% transparent
    watermark_alpha = watermark.split()[3]  # Extract the alpha channel
    watermark_alpha = watermark_alpha.point(
        lambda p: int(p * 0.7)
    )  # Reduce opacity to 70%
    watermark.putalpha(watermark_alpha)

    # Calculate position for bottom-right corner
    position = (
        imagedata.size[0] - watermark.size[0],
        imagedata.size[1] - watermark.size[1],
    )

    # Create a new image with an alpha channel to combine the watermark
    transparent = Image.new("RGBA", imagedata.size, (0, 0, 0, 0))
    transparent.paste(imagedata.convert("RGBA"), (0, 0))
    transparent.paste(watermark, position, watermark)

    # Return the final image
    return transparent.convert("RGB")


def make_story_post(json_story):
    """Makes the markdown story post"""
    # Write Markdown content to a temporary file
    story_data = json_story["picked_article"]
    ai_data = json_story["ai_img"]
    editedstory = editerai.alter_story(story_data["content"])
    story_data["ai_description"] = editedstory["body"]
    published_at = json_story["picked_article"]["publishedAt"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp_file:
        tmp_file_path = tmp_file.name

    logging.info("Temp Path file %s", str(tmp_file_path))

    with open(tmp_file_path, "w", encoding="utf-8") as tmpmd:
        formated_pub_date = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        ).strftime("%d/%m/%Y %I:%M %p")
        tmpmd.write("+++\n")
        tmpmd.write(f"title = '{story_data['title']}'\n")
        tmpmd.write(f"id ='{json_story.get('eventid')}'\n")
        tmpmd.write(f"story_date = '{published_at}'\n")
        tmpmd.write(f"date = '{datetime.now(timezone.utc).astimezone().isoformat()}'\n")
        tmpmd.write("draft = false\n")
        tmpmd.write(f"author = '{story_data['author']}'\n")
        tmpmd.write(f"source = '{story_data['source']}'\n")
        tmpmd.write("+++\n")
        tmpmd.write("## About the story\n\n")
        tmpmd.write(f"- Story Source: [{story_data['source']}]({story_data['url']})\n")
        tmpmd.write(f"- Story Author: {story_data['author']}\n")
        tmpmd.write(f"- Published Date: {formated_pub_date}\n")
        tmpmd.write(
            f"- Picked Date: {datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %I:%M %p")}\n"
        )
        tmpmd.write("\n")
        tmpmd.write(f"{story_data['ai_description']}\n")
        tmpmd.write("\n")
        tmpmd.write("\n")
        tmpmd.write("\n## AI info for image\n\n")
        tmpmd.write(f"- Image Model used: {ai_data['img_model']}\n")
        tmpmd.write(f"- Promt Model used: {ai_data['promt_model']}\n")
        tmpmd.write("\n")
        tmpmd.write("\n### Promt Used\n")
        tmpmd.write(f"{ai_data['promt']}\n")
        tmpmd.write("\n")
        tmpmd.write(
            f"\n## AI info for Story (Total: {story_data['aiscore']['score']})\n"
        )
        tmpmd.write("\n")
        tmpmd.write("\n")

        for aiscore in story_data["aiscore"]["response"]:
            tmpmd.write(f"- Model {aiscore['model_id']} Scored {aiscore['score']}\n\n")
    return tmp_file_path


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
                Name=os.getenv("SSM_PARAMETER_NAME") or "/newsaiimg/dev/settings",
                WithDecryption=True,
            )["Parameter"]["Value"]
        )
        s3_client = boto3.client("s3")
        logging.info(
            "Getting josn data: %s",
            f"s3://{ssm_data['ais3bucket']}/aiimg/{event.get('event_id')}/main.json",
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
            f"s3://{ssm_data['ais3bucket']}/aiimg/{event.get('event_id')}/newsimage.png",
        )
        news_image = Image.open(
            BytesIO(
                s3_client.get_object(
                    Bucket=ssm_data["ais3bucket"],
                    Key=f"aiimg/{event.get('event_id')}/newsimage.png",
                )["Body"].read()
            )
        )
        # Save the image to a test file
        resize_and_save_image(
            image=watermark_image(news_image),
            width=500,
            s3info={
                "bucket": ssm_data["ais3bucket"],
                "key": f"website/content/images/{json_data.get('eventid')}/main.jpg",
            },
        )
        resize_and_save_image(
            image=news_image,
            width=70,
            s3info={
                "bucket": ssm_data["ais3bucket"],
                "key": f"website/content/images/{json_data.get('eventid')}/thum.jpg",
            },
        )
        logging.info("AI the story info")
        # Upload the temporary file to S3
        with open(make_story_post(json_data), "rb") as tmp_file:
            s3_client.put_object(
                Bucket=ssm_data["ais3bucket"],
                Key=f"website/content/post/{json_data.get('eventid')}.md",
                Body=tmp_file,
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
