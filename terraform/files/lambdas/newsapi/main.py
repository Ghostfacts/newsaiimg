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
    if response.status_code == 200:
        logging.debug("Got content")
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")
        if soup.find(class_="episode-panel__meta"):
            return "was not able to retive story"
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
            logging.debug("Striped out conetent")
            return "".join(full_article)
        return "was not able to retive story"
    else:
        logging.error("Failed to retrieve webpage: %s", response.status_code)
        soup = None
        return "was not able to retive story"


ban_words = ["football", "sports", "Broadcast", "sport", "stabbings", "stab"]


# main
def lambda_handler(event, context):  # pylint: disable=W0613
    """Main function for the lambda"""
    bedrock = genai.Bedrock(region="eu-west-2")
    today, yesterday = get_today_and_yesterday_dates()
    newsapi_key = get_secret(
        secret_name=os.getenv("secrect_name", "newsaiimg-dev-ssm-newsapi"),
        region_name=os.getenv("region_name", "eu-west-2"),
    )["token"]
    newsapi = NewsApiClient(api_key=newsapi_key)
    filtred_article_list = []
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
        for article in all_articles["articles"]:
            article_check = True
            article["content"] = get_fullstory(article["url"])
            if (
                str(article["author"]).lower() == "none"
                or str(article["author"]).lower() == "null"
            ):
                logging.info(
                    "Removing story %s -> author (%s) is not valied",
                    article["title"],
                    str(article["author"]).lower(),
                )
                article_check = False
            if (
                article["content"] == "was not able to retive story"
                and article_check is True
            ):
                logging.info(
                    "Removing story %s -> cant get full story", article["title"]
                )
                article_check = False
            for ban_word in ban_words:
                if (
                    ban_word in article["content"]
                    or ban_word in article["title"]
                    and article_check is True
                ):
                    logging.info(
                        "Removing story: %s -> baned word (%s) found",
                        article["title"],
                        ban_word,
                    )
                    article_check = False
            if article_check is False:
                all_articles["articles"].remove(article)
            else:
                article["aiscors"] = bedrock.news_reviews(article["content"])
                article["airesult"] = {"result": "not_registred", "score": 0}
                for aires in article["aiscors"]:
                    article["airesult"]["score"] = (
                        aires["results"]["score"] + aires["results"]["score"]
                    )
                    if aires["results"]["result"] == "fail":
                        article["airesult"]["result"] = "Failed"
                        logging.info(
                            "Story Failed AI Check: %s, Why: %s",
                            article.get("title", "missing"),
                            aires["results"].get("reson", ""),
                        )
                        article_check = False
                if aires["results"]["score"] <= 0:
                    logging.info("Removing story %s -> AI score is 0", article["title"])
                    article_check = False
                # Final check to see if story shoud be added
                if article_check is False:
                    all_articles["articles"].remove(article)
                else:
                    logging.info("Adding story: %s", article["title"])
                    article["id"] = len(filtred_article_list)
                    article["picked"] = "false"
                    filtred_article_list.append(article)
    logging.info(
        "Total articles recived %s vs Totel after sorted %s",
        len(all_articles["articles"]),
        len(filtred_article_list),
    )
    choose_article = max(filtred_article_list, key=lambda x: x["airesult"]["score"])
    logging.info("Story ID picked %s", choose_article["id"])
    filtred_article_list[choose_article["id"]]["picked"] = "true"
    choose_article["source"] = choose_article["source"]["id"]
    choose_article.pop("picked", None)
    choose_article.pop("aiscors", None)
    choose_article.pop("airesult", None)
    choose_article.pop("id", None)
    return {
        "event_id": str(generate_custom_uuid()),
        "picked_article": choose_article,
        "all_articles": filtred_article_list,
        "logStreamName": getattr(context, "log_stream_name", None),
    }


# testing
if __name__ == "__main__":
    print(json.dumps(lambda_handler(None, None), indent=4))
