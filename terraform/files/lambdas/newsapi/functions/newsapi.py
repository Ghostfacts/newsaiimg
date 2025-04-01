"""News API module"""

import logging
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


class Newsapi:
    """To run all newsapi things"""

    def __init__(self, apikey):
        """To enable action and add key"""
        self.apipath = "https://newsapi.org/v2/"
        self.headers = {"X-Api-Key": apikey}  # Replace with your API key

    def get_headlines(self, country="eu"):
        """Retrive the top headline stores"""
        base_url = f"{self.apipath}/top-headlines"
        query_params = f"?domains=bbc.co.uk" f"&language={country}"
        url = f"{base_url}{query_params}"
        response = requests.get(url, headers=self.headers, timeout=20)
        if response.status_code != 200:
            logging.error("Error fetching news: %s", response.status_code)
        return response

    def get_stories(self, country="en"):
        """grathing the needed stores from the newsapi"""
        stories = {"articles": [], "status": "unknow", "totalResults": 0}
        dates = self.__gendate()
        base_url = f"{self.apipath}/everything"
        query_params = (
            f"?domains=bbc.co.uk"
            f"&from={dates['from']}"
            f"&to={dates['to']}"
            f"&sortBy=popularity"
            f"&language={country}"
        )
        url = f"{base_url}{query_params}"
        response = requests.get(url, headers=self.headers, timeout=20)
        if response.status_code != 200:
            logging.error("Error fetching news: %s", response.status_code)
        else:
            logging.info("Fetched news successfully")
            stories["status"] = response.json()["status"]
            stories["totalResults"] = response.json()["totalResults"]
            for article in response.json()["articles"]:
                article["source"] = article["source"]["id"]
                if article["author"] is None:
                    continue
                if article["url"] is None:
                    continue
                if (
                    re.search(r"\barticles\b", article["url"])
                    and article["source"] == "bbc-news"
                ):
                    article["content"] = self.__full_article(article["url"])
                else:
                    article["content"] = None
                # checks if their is content to be used
                if article["content"] is None:
                    continue
                stories["articles"].append(article)
        return stories
        # return response.json()['articles']

    def __gendate(self):
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        return {"from": yesterday.strftime("%Y-%m-%d"), "to": now.strftime("%Y-%m-%d")}

    def __remove_specific_href_tags(self, text, keywords):
        """Removes unwatned href info from story"""
        # Define the regex pattern to find <a> tags with specific keywords in the href attribute
        pattern = (
            r'<a\s+[^>]*href="[^"]*(' + "|".join(keywords) + r')[^"]*"[^>]*>.*?<\/a>'
        )
        # Substitute the matching <a> tags with an empty string
        cleaned_text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return cleaned_text

    def __full_article(self, url):
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
                        par_text = self.__remove_specific_href_tags(par_text, keywords)
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
