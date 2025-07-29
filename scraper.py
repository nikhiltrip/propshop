# scraper.py

import requests
from bs4 import BeautifulSoup

# The URL of the site we want to scrape
# Note: We start with the main page. Getting to the specific sports boards is a later step.
url = "https://www.prizepicks.com/"

# A 'User-Agent' tells the website what kind of browser is visiting.
# It's good practice to set this to look like a real browser.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("Attempting to fetch the website...")

try:
    # Make the request to the website
    response = requests.get(url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        print("Successfully fetched the website!")

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the <title> tag of the page and print it
        page_title = soup.find('title').text
        print(f"The page title is: '{page_title}'")

    else:
        print(f"Failed to fetch website. Status code: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

