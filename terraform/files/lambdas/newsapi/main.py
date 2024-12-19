import os
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from newsapi.newsapi_client import NewsApiClient
from bs4 import BeautifulSoup
import requests
import boto3
from botocore.exceptions import ClientError


if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

#functions

def get_secret(secret_name, region_name='eu-west-1'):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        # Retrieve the secret
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logging.error("Secret %s not found",secret_name)
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            logging.error("The request to retrieve the secret %s was invalid.",secret_name)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            logging.error("The parameter for the request to retrieve the secret %s was invalid.",secret_name)
        else:
            logging.error("Unexpected error occurred: %s",e)
        return None
    else:
        # Parse and return the secret JSON string
        secret = json.loads(response['SecretString'])
        return secret


def get_today_and_yesterday_dates():
    # Get today's date
    today_date = datetime.today().date()
    # Get yesterday's date by subtracting one day from today
    yesterday_date = today_date - timedelta(days=1)
    formatted_today_date = today_date
    formatted_yesterday_date = yesterday_date   
    return formatted_today_date, formatted_yesterday_date

def get_fullstory(url):
    # Send an HTTP GET request to the URL
    response = requests.get(url)
    logging.debug("retriveing url %s",url)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        logging.debug("Got content")
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('article')
        if soup.find(class_="episode-panel__meta"):
            return "was not able to retive story"
        if article:
            logging.debug("Retrived article")
            full_article=[]
            for img_tag in article.find_all('img'):
                img_tag.extract()  # Remove the <img> tag from the BeautifulSoup object
            text_elements = soup.find_all(attrs={'data-component': 'text-block'})
            for text_element in text_elements:
                logging.debug("Add article text")
                article_text= text_element.get_text(separator='\n', strip=True).encode('utf-8')
                full_article.append (
                    article_text.decode('utf-8')
                )
            logging.debug("Striped out conetent")
            return ''.join(full_article)
        return "was not able to retive story"
    else:
        logging.error("Failed to retrieve webpage: %s",response.status_code)
        soup = None
        return "was not able to retive story"


ban_words=[
    "football",
    "sports",
    "Broadcast",
    "sport"
]


#main
def lambda_handler(event, context):
    today, yesterday = get_today_and_yesterday_dates()
   newsapi_key = get_secret(os.getenv('secrect_name'))
    selected_articles =[]
    logging.info("Grathing all news articles in date range %s to %s",yesterday.strftime('%Y-%m-%d'),today.strftime('%Y-%m-%d'))
    all_articles = newsapi.get_everything(
                                        sources='bbc-news',
                                        domains='bbc.co.uk',
                                        from_param=yesterday.strftime('%Y-%m-%d'),
                                        to=today.strftime('%Y-%m-%d'),
                                        language='en',
                                        sort_by='relevancy'
                                        )
    #get the full story and drop podcasts
    if all_articles['status'] != "ok":
        logging.error("API status returned error")
    elif len(all_articles['articles']) == 0:
        logging.info("No Stories where returned")
    elif all_articles['status'] == "ok" and len(all_articles['articles']) > 0:
        for article in all_articles['articles']:
            article_check = True
            article['content'] = get_fullstory(article['url'])
            if str(article['author']).lower() == "none" or str(article['author']).lower() == "null":
                logging.info("Removing story %s -> author (%s) is not valied",article['title'],str(article['author']).lower())
                article_check = False        
            if article['content'] == "was not able to retive story" and article_check is True:
                logging.info("Removing story %s -> cant get full story",article['title'])
                article_check = False
            for ban_word in ban_words:
                if ban_word in article['content'] and article_check is True:
                    logging.info("Story: %s -> cotains an baned word (%s)",article['title'],ban_word)
                    article_check = False
            if article_check is False:
                all_articles['articles'].remove(article)
            else:
                logging.info("Story: %s -> adding",article['title'])
                selected_articles.append(article)
    logging.info("Total articles recived %s vs Totel after sorted %s",len(all_articles['articles']), len(selected_articles))
    print(json.dumps(selected_articles, indent=4))

#for testing
lambda_handler(1,2)