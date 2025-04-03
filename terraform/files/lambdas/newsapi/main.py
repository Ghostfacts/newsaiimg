"""Lambda function for getting sotries and filtering them"""

import json
import logging
import os
import random
import re
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from functions import genai, newsapi

if len(logging.getLogger().handlers) > 0:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

bedrock_client = genai.Bedrock(region="eu-west-2")


# functions
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

    return custom_uuid


def upload_to_s3(file_path, bucket_name, s3_key):
    """Upload a file to an S3 bucket"""
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(file_path, bucket_name, s3_key)
        logging.info("Uploading %s to s3://%s/%s", file_path, bucket_name, s3_key)
    except Exception as e:
        logging.error("Failed to upload %s to S3: %s", file_path, e)
        raise


def get_secret(secret_name, region_name="eu-west-1"):
    """Retrives the secret from AWS Secrets Manager"""
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    secret = None
    try:
        # Retrieve the secret
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            logging.error("Secret %s not found", secret_name)
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            logging.error(
                "The request to retrieve the secret %s was invalid.", secret_name
            )
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            logging.error(
                "The parameter for the request to retrieve the secret %s was invalid.",
                secret_name,
            )
        else:
            logging.error("Unexpected error occurred: %s", e)
    else:
        # Parse and return the secret JSON string
        secret = json.loads(response["SecretString"])
    return secret


def filter_article(article):
    """Filter the article"""
    ban_words = [
        "football",
        "sports",
        "Broadcast",
        "sport",
        "stabbings",
        "stab",
        "drug",
        "drugs",
        "pill",
        "lottery",
    ]
    author_black_list = []
    # logging.info(article)
    article_check = True
    if article["content"] == "" or article["content"] is None:
        logging.info("Removing story %s -> cant get full story", article["title"])
        article_check = False
    if (
        str(article["author"]).lower() == "none"
        or str(article["author"]).lower() == "null"
        or str(article["author"]).lower() in author_black_list
    ):
        logging.info("Removing story %s -> Unknow Author", article["title"])
        article_check = False
    for ban_word in ban_words:
        if re.search(ban_word, article["title"], flags=re.IGNORECASE):
            logging.info(
                "Removing story %s -> Bad word (%s) in title",
                article["title"],
                ban_word,
            )
            article_check = False
        if re.search(ban_word, article["content"], flags=re.IGNORECASE):
            logging.info(
                "Removing story %s -> Bad word (%s) in content",
                article["title"],
                ban_word,
            )
            article_check = False
    return article_check


def ai_scoring(article):
    """Using AI to score the article"""
    article["ai_results"] = {}
    article["ai_results"]["response"] = []
    for ainew_review in bedrock_client.news_reviews(article["content"]):
        finresulst = ainew_review.get("results", "")
        article["ai_results"] = {"score": 0, "aicheck": "pass", "response": []}
        article["ai_results"]["response"].append(
            {
                "model_id": ainew_review.get("model_id", "missing"),
                "score": finresulst.get("score", "missing"),
                "reson": finresulst.get("reason", "missing"),
                "aicheck": finresulst.get("result", "missing"),
            }
        )
        article["ai_results"]["score"] = article["ai_results"][
            "score"
        ] + finresulst.get("score", "missing")
        if finresulst.get("result", "missing") == "fail":
            article["ai_results"]["aicheck"] = "failed"
    if article["ai_results"].get("score", 0) <= 0:
        article["ai_results"]["aicheck"] = "failed"
    return article["ai_results"]


def article_picker(articles):
    """Will look at the articles scors and pick the right one"""
    logging.info("Selecting article")
    max_record = max(articles, key=lambda item: item["ai_results"]["score"])
    logging.info(
        "Picked article (%s) with an score of %s",
        max_record["title"],
        max_record["ai_results"]["score"],
    )
    max_record.pop("ai_results")
    return max_record


# main
def lambda_handler(event, context):  # pylint: disable=W0613
    """Main function for the lambda"""
    # ssm_client = boto3.client("ssm", region_name="eu-west-2")
    # ssm_data = json.loads(
    #     ssm_client.get_parameter(
    #         Name=os.getenv("SSM_PARAMETER_NAME") or "/newsaiimg/dev/settings",
    #         WithDecryption=True,
    #     )["Parameter"]["Value"]
    # )
    # temp_dir = (
    #     tempfile.TemporaryDirectory()  # pylint: disable=R1732 #dont want to use an with
    # )
    newsapi_key = get_secret(
        secret_name=os.getenv("secrect_name", "newsaiimg-dev-ssm-newsapi"),
        region_name=os.getenv("region_name", "eu-west-2"),
    )["token"]

    newsapi_client = newsapi.Newsapi(newsapi_key)
    all_articles = newsapi_client.get_stories()
    # get the full story and drop podcasts
    if all_articles["status"] != "ok":
        logging.error("API status returned error")
    elif len(all_articles["articles"]) == 0:
        logging.info("No Stories where returned")
    elif all_articles["status"] == "ok" and len(all_articles["articles"]) > 0:
        # Get the full story from the BBC
        filtred_articles = []
        for article in all_articles["articles"]:
            add_story = False
            article["ai_results"] = ai_scoring(article)
            ai_score = 0
            for scores in article["ai_results"]["response"]:
                logging.info(
                    "AI Score: %s, Modle %s", scores["score"], scores["model_id"]
                )
                ai_score = ai_score + scores.get("score", 0)
            logging.info("Total AI score: %s", ai_score)
            # Basic filtering
            if article["ai_results"].get("aicheck", "failed") == "failed":
                logging.warning("Sory failed AI check %s", article["title"])
            elif article["ai_results"].get("aicheck", "failed") == "pass":
                add_story = True
                logging.debug("AI check Passed %s", article["title"])

            if add_story is True:
                filtred_articles.append(article)
        logging.info(
            "Leaving %s articles out of %s",
            len(filtred_articles),
            len(all_articles["articles"]),
        )
    # Need to pick an winner

    return {
        "event_id": str(generate_custom_uuid()),
        "picked_article": article_picker(filtred_articles),
        "all_articles": filtred_articles,
        "logStreamName": getattr(context, "log_stream_name", None),
    }
