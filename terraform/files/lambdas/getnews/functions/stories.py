"""News API module"""

import logging
import re
import sys
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


class Newsapi:
    """To run all newsapi things"""

    # internal ones
    def __init__(self, apitoken):
        logging.info("Creating Newsapi instance")
        self.apiurl = "https://newsapi.org/v2/"
        self.headers = {"X-Api-Key": apitoken}  # Replace with your API key
        self.timeout = 20
        self.filter_words = [
            # Violence-related
            "murder",
            "killing",
            "killed",
            "stabbed",
            "shooting",
            "gun",
            "assault",
            "attack",
            "bomb",
            "terrorism",
            "terrorist",
            "massacre",
            "hostage",
            "execute",
            "executed",
            "crime",
            "riot",
            "lynching",
            "beheaded",
            "torture",
            "rape",
            "arson",
            "war",
            "conflict",
            "explosion",
            # Drugs / Substance Abuse
            "drugs",
            "cocaine",
            "heroin",
            "meth",
            "fentanyl",
            "overdose",
            "trafficking",
            "narcotics",
            "drug lord",
            "cartel",
            "substance abuse",
            "opium",
            "opioid",
            "addicted",
            "addiction",
            "rehab",
            "smuggling",
            "cannabis",
            "marijuana",
            "weed",
            "crack",
            # Politics / Government
            "government",
            "parliament",
            "senate",
            "congress",
            "politician",
            "politics",
            "campaign",
            "election",
            "vote",
            "president",
            "minister",
            "lawmaker",
            "legislation",
            "policy",
            "referendum",
            "impeachment",
            "administration",
            "political party",
            "government shutdown",
            "prime minister",
            "opposition",
            "democrat",
            "republican",
            "tory",
            "labour",
            # Extra suggestions
            "protest",
            "suicide",
            "execution",
            "hate",
            "racism",
            "abuse",
            "fraud",
            "corruption",
            "scandal",
            "hate crime",
            "human trafficking",
        ]
        self.filter_authors = [
            "BBC World Service",
            "BBC Radio",
            "BBC Radio 4",
            "BBC Radio 5 Live",
            "BBC Radio 1",
            "BBC Radio 2",
            "BBC Radio 3",
            "BBC Radio 6 Music",
            "BBC Radio 7",
            "BBC Radio 8",
            "BBC News",
        ]

    def __remove_specific_href_tags(self, text, keywords):
        """Removes unwatned href info from story"""
        # Define the regex pattern to find <a> tags with specific keywords in the href attribute
        pattern = (
            r'<a\s+[^>]*href="[^"]*(' + "|".join(keywords) + r')[^"]*"[^>]*>.*?<\/a>'
        )
        # Substitute the matching <a> tags with an empty string
        cleaned_text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return cleaned_text

    def __filter_story(self, article):
        """Filter the stories to remove the ones we dont want"""
        result = True
        if article.get("author", None) is None:
            logging.info("Removing story %s -> Unknow Author", article["title"])
            result = False
        elif (
            str(article.get("author", "None")).lower()
            in str(self.filter_authors).lower()
        ):
            logging.info("Removing story %s -> Bad Author", article["title"])
            result = False
        elif article.get("title", None) is None:
            logging.info("Removing story %s -> No title", article["title"])
            result = False
        elif article.get("content", None) is None:
            logging.info("Removing story %s -> No content", article["title"])
            result = False
        elif article.get("description", None) is None:
            logging.info("Removing story %s -> No description", article["title"])
            result = False
        elif article.get("url", None) is None:
            logging.info("Removing story %s -> No url", article["title"])
            result = False

        for word in self.filter_words:
            if word in str(article.get("title", "None")).lower():
                logging.info(
                    "Removing story %s -> Bad word (%s) in title",
                    article["title"],
                    word,
                )
                result = False
            if word in str(article.get("content", "None")).lower():
                logging.info(
                    "Removing story %s -> Bad word (%s) in content",
                    article["title"],
                    word,
                )
                result = False
                break
            if word in str(article.get("description", "None")).lower():
                logging.info(
                    "Removing story %s -> Bad word (%s) in description",
                    article["title"],
                    word,
                )
                result = False
                break
        return result

    # main functions
    def get_headlines(self, country="eu"):
        """Retrive the top headline stores"""
        try:
            base_url = f"{self.apiurl}/top-headlines"
            query_params = f"?domains=bbc.co.uk" f"&language={country}"
            url = f"{base_url}{query_params}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            logging.info("Fetched headlines successfully")
            logging.info("Total Stories: %s", response.json().get("totalResults", 0))
            if response.json().get("totalResults", 0) == 0:
                raise ValueError("No stories found")

            story_list = []
            for article in response.json().get("articles", []):
                if self.__filter_story(article) is True:
                    article["source"] = article["source"]["id"]
                    story_list.append(article)

            logging.info("Total after Filtering: %s", len(story_list))

            return story_list

        except ValueError as ve:
            # Handle value errors (e.g., no stories found)
            logging.error("Value error occurred: %s", ve)
            return None
        except requests.exceptions.HTTPError as http_err:
            # Handle HTTP errors (e.g., 404, 500, etc.)
            logging.error(
                "HTTP error occurred: %s - Status Code: %s",
                http_err,
                response.status_code,
            )
            sys.exit(1)  # Exit the script with a failure code (1)

        except requests.exceptions.Timeout as timeout_err:
            # Handle timeout errors
            logging.error("Request timed out: %s", timeout_err)
            sys.exit(1)  # Exit the script with a failure code (1)

        except requests.exceptions.ConnectionError as conn_err:
            # Handle connection errors (e.g., network issues)
            logging.error("Connection error occurred: %s", conn_err)
            sys.exit(1)  # Exit the script with a failure code (1)

        except requests.exceptions.RequestException as req_err:
            # Catch all other requests exceptions
            logging.error("An error occurred while fetching news: %s", req_err)
            sys.exit(1)  # Exit the script with a failure code (1)

    def get_stories(self, daysold=1, country="en"):  # pylint: disable=R1710
        """grathing the needed stores from the newsapi"""
        try:
            story_list = []
            query_params = (
                f"?domains=bbc.co.uk"
                f"&from={(datetime.now() - timedelta(days=daysold)).strftime('%Y-%m-%d')}"
                f"&to={datetime.now().strftime('%Y-%m-%d')}"
                f"&sortBy=popularity"
                f"&language={country}"
            )
            url = f"{self.apiurl}/everything{query_params}"
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            logging.info("Fetched stories successfully")
            logging.info("Total Stories: %s", response.json().get("totalResults", 0))
            if response.json().get("totalResults", 0) == 0:
                raise ValueError("No stories found")

            for article in response.json().get("articles", []):
                if self.__filter_story(article) is True:
                    article["source"] = article["source"]["id"]
                    article["content"] = self.get_full_content(article.get("url"))
                    story_list.append(article)
            logging.info("Total after Filtering: %s", len(story_list))
            return story_list

        except ValueError as ve:
            # Handle value errors (e.g., no stories found)
            logging.error("Value error occurred: %s", ve)
        except requests.exceptions.HTTPError as http_err:
            # Handle HTTP errors (e.g., 404, 500, etc.)
            logging.error(
                "HTTP error occurred: %s - Status Code: %s",
                http_err,
                response.status_code,
            )
            sys.exit(1)  # Exit the script with a failure code (1)

        except requests.exceptions.Timeout as timeout_err:
            # Handle timeout errors
            logging.error("Request timed out: %s", timeout_err)
            sys.exit(1)  # Exit the script with a failure code (1)

        except requests.exceptions.ConnectionError as conn_err:
            # Handle connection errors (e.g., network issues)
            logging.error("Connection error occurred: %s", conn_err)
            sys.exit(1)  # Exit the script with a failure code (1)

        except requests.exceptions.RequestException as req_err:
            # Catch all other requests exceptions
            logging.error("An error occurred while fetching news: %s", req_err)
            sys.exit(1)  # Exit the script with a failure code (1)

    def get_full_content(self, url):
        """Retrive the full story"""
        logging.debug("Retreving story from url: %s", str(url))
        try:
            result = None
            storysite = requests.get(url=url, timeout=self.timeout)
            storysite.raise_for_status()
            soup = BeautifulSoup(storysite.text, "html.parser")
            article = soup.find("article")
            if article:
                # Removing all images from the article
                keywords = ["facebook", "twitter", "instagram"]
                full_article = []
                for img_tag in article.find_all("img"):
                    img_tag.extract()  # Remove the <img> tag from the BeautifulSoup object
                text_elements = soup.find_all(attrs={"data-component": "text-block"})
                for text_element in text_elements:
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
        except requests.exceptions.HTTPError as http_err:
            # Handle HTTP errors (e.g., 404, 500, etc.)
            logging.error(
                "HTTP error occurred: %s - Status Code: %s",
                http_err,
                storysite.status_code,
            )
            sys.exit(1)  # Exit the script with a failure code (1)
        return result
