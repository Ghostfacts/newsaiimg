"""Lambda function for getting sotries and filtering them"""

import json
import logging
import os
import random
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from functions import aiscoring, stories  # pylint: disable=E0611

if len(logging.getLogger().handlers) > 0:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


# Functions
def generate_custom_uuid():
    """Create an uniquuid"""
    # Get the current date and time
    now = datetime.today()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")

    # Generate a random number
    random_number = random.randint(1000, 9999)

    # Combine date, time, and random number to form the UUID
    custom_uuid = f"{date_str}-{time_str}-{random_number}"
    logging.info("Generated UUID: %s", custom_uuid)
    return custom_uuid


# main code
def lambda_handler(event, context):  # pylint: disable=W0613,R1710
    """Main lambda handler Where it all starts"""
    newsai = aiscoring.AWSai(region=os.getenv("region") or "eu-west-2")
    # Defult Return info
    result = {
        "statusCode": 200,
        "body": json.dumps("Hello from Lambda!"),
    }
    try:
        # genertaes the basic jasondata file
        json_data = {"eventid": str(generate_custom_uuid())}
        # Get the event data from the event
        result["eventid"] = json_data["eventid"]
        # Returns the ssm prmater for all info
        ssm_client = boto3.client("ssm", region_name=os.getenv("region") or "eu-west-2")
        ssm_data = json.loads(
            ssm_client.get_parameter(
                Name=os.getenv("SSM_PARAMETER_NAME") or "/newsaiimg/dev/lambdasettings",
                WithDecryption=True,
            )["Parameter"]["Value"]
        )
        # Ok need to get the Newsapi info
        newsapi = stories.Newsapi(
            apitoken=ssm_data["newsapi_token"],
        )
        # Get the stories
        json_data["all_articles"] = newsapi.get_stories()
        # json_data["all_articles"] = newsapi.get_headlines()

        # Get the count of articles
        if json_data["all_articles"] is not None:
            json_data["total_articles"] = len(json_data["all_articles"])
            # need to pick the winner article now
            for article in json_data["all_articles"]:
                logging.info(
                    "Starting to AI score on:%s", article.get("title", "Unknow")
                )
                article["aiscore"] = newsai.score_story(article)
                logging.debug("AI results: %s", article["aiscore"])
                logging.info("Sleeping for 5 seconds")
                time.sleep(5)
        else:
            json_data["total_articles"] = 0

        for index, rt in enumerate(json_data.get("all_articles", [])):
            logging.debug(
                "Index: %s, Score: %s - AI Check: %s",
                index,
                rt["aiscore"]["score"],
                rt["aiscore"]["aicheck"],
            )
            # Find the article with the highest score
            json_data["picked_article"] = max(
                json_data["all_articles"],
                key=lambda x: (
                    x["aiscore"]["score"]
                    if "aiscore" in x and "score" in x["aiscore"]
                    else float("-inf")
                ),
            )
            # Log the article with the highest score
        if json_data.get("picked_article") is not None:
            logging.info(
                "Winner Article: %s With Score %s and check: %s",
                json_data["picked_article"].get("title", "Unknown"),
                json_data["picked_article"]["aiscore"]["score"],
                json_data["picked_article"]["aiscore"]["aicheck"],
            )
        else:
            logging.error("No Winning storry found")

        # save the content to s3
        s3_client = boto3.client("s3")
        s3_client.put_object(
            Bucket=ssm_data["ais3bucket"],
            Key=f"aiimg/{json_data.get('eventid')}/main.json",
            Body=json.dumps(json_data, indent=2).encode("utf-8"),
        )
        logging.info(
            "Main file saved to s3 at %s", f'aiimg/{json_data.get("eventid")}/main.json'
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
    # except Exception as e:  # pylint: disable=W0718
    #     logging.error("General: %s", str(e))
    #     result["statusCode"] = 500
    #     result["error"] = json.dumps({"error": str(e)})

    # Return the result
    return result
