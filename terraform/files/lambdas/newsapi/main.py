"""Lambda function for getting sotries and filtering them"""

import json
import logging
import os
import random
import re
from datetime import datetime, timedelta

import boto3
import genai
import requests
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from newsapi.newsapi_client import NewsApiClient

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


def remove_specific_href_tags(text, keywords):
    """Removes unwatned href info from story"""
    # Define the regex pattern to find <a> tags with specific keywords in the href attribute
    pattern = r'<a\s+[^>]*href="[^"]*(' + "|".join(keywords) + r')[^"]*"[^>]*>.*?<\/a>'
    # Substitute the matching <a> tags with an empty string
    cleaned_text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return cleaned_text


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


def get_today_and_yesterday_dates():
    """Get today's and yesterday's date"""
    # Get today's date
    today_date = datetime.today().date()
    # Get yesterday's date by subtracting one day from today
    yesterday_date = today_date - timedelta(days=1)
    formatted_today_date = today_date
    formatted_yesterday_date = yesterday_date
    return formatted_today_date, formatted_yesterday_date


def get_fullstory(url):
    """Get the full story from the URL"""
    # Send an HTTP GET request to the URL
    response = requests.get(url=url, timeout=20)
    logging.debug("retriveing url %s", url)
    # Check if the request was successful (status code 200)
    keywords = ["facebook", "twitter", "instagram"]
    if response.status_code == 200:  # pylint: disable=R1705
        logging.debug("Got content")
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")
        if soup.find(class_="episode-panel__meta"):
            logging.warning("Found the episode-panel__meta class")
            result = None
        if article:
            logging.debug("Retrived article")
            full_article = []
            for img_tag in article.find_all("img"):
                img_tag.extract()  # Remove the <img> tag from the BeautifulSoup object
            text_elements = soup.find_all(attrs={"data-component": "text-block"})
            for text_element in text_elements:
                logging.debug("Add article text")
                for par_element in text_element.find_all("p"):
                    par_text = par_element.get_text(separator="\n", strip=True)
                    par_text = remove_specific_href_tags(par_text, keywords)
                    par_text = par_text.replace("\n", " ")
                    par_text = par_text.replace("\r", " ")
                    if re.search(
                        r"Follow BBC", par_text, flags=re.IGNORECASE
                    ) or re.search(r"@BBC", par_text, flags=re.IGNORECASE):
                        break
                    full_article.append(f" {par_text}")
            result = "".join(full_article)
    else:
        logging.error("Failed to retrieve webpage: %s", response.status_code)
        soup = None
        result = None
    return result  # Results of the info


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
    max_record.pop("pendingremove")
    max_record.pop("ai_results")
    return max_record


# main
def lambda_handler(event, context):  # pylint: disable=W0613
    """Main function for the lambda"""
    today, yesterday = get_today_and_yesterday_dates()
    newsapi_key = get_secret(
        secret_name=os.getenv("secrect_name", "newsaiimg-dev-ssm-newsapi"),
        region_name=os.getenv("region_name", "eu-west-2"),
    )["token"]
    newsapi = NewsApiClient(api_key=newsapi_key)
    logging.info(
        "Grathing all news articles with in date range from %s to %s",
        yesterday.strftime("%Y-%m-%d %H:%M:%S"),
        today.strftime("%Y-%m-%d %H:%M:%S"),
    )
    all_articles = newsapi.get_everything(
        sources="bbc-news",
        domains="bbc.co.uk",
        from_param=yesterday.strftime("%Y-%m-%d"),
        to=today.strftime("%Y-%m-%d"),
        language="en",
        sort_by="relevancy",
    )
    # get the full story and drop podcasts
    if all_articles["status"] != "ok":
        logging.error("API status returned error")
    elif len(all_articles["articles"]) == 0:
        logging.info("No Stories where returned")
    elif all_articles["status"] == "ok" and len(all_articles["articles"]) > 0:
        # Get the full story from the BBC
        filtred_articles = []
        for article in all_articles["articles"]:
            # Basic filtering

            article["pendingremove"] = False
            if re.search(
                r"BBC World Service", article["description"], flags=re.IGNORECASE
            ):
                logging.info(
                    "Removing news story %s as its BBC World Service", article["title"]
                )
                article["pendingremove"] = True

            if article["pendingremove"] is False:
                logging.info(
                    "retriving Full article from website (%s)", article["title"]
                )
                article["content"] = get_fullstory(article["url"])
                if article["content"] is None:
                    logging.info(
                        "Removing news story %s as no content", article["title"]
                    )
                    article["pendingremove"] = True
                elif filter_article(article) is False:
                    logging.info(
                        "Removing news story %s due to basic filter", article["title"]
                    )
                    article["pendingremove"] = True

                if article["pendingremove"] is False:
                    article["source"] = article["source"]["id"]
                    # run AI filtering (using ai to score)
                    logging.info("retriving AI scoring (%s)", article["title"])
                    article["ai_results"] = ai_scoring(article)
                    if article["ai_results"].get("aicheck", "missing") == "failed":
                        logging.info(
                            "Removing news story %s failed AI check", article["title"]
                        )
                        logging.info("AIdata: %s", article["ai_results"])
                    else:
                        logging.info("Adding news story %s to list", article["title"])
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
