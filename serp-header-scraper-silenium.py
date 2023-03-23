from bs4 import BeautifulSoup
import csv
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import requests
import re
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException

def search_google(query, num_results, lang, ua):
    driver = webdriver.Chrome()
    driver.get(f"https://www.google.com/search?q={query}&num={num_results}&hl={lang}")

    input("Solve the CAPTCHA if required, then press Enter to continue...")

    search_results = driver.find_elements(By.CSS_SELECTOR, ".g")
    results = []

    for index, result in enumerate(search_results):
        url = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
        title = result.find_element(By.CSS_SELECTOR, "h3").text
        try:
            description = result.find_element(By.CSS_SELECTOR, ".IsZvec").text
        except NoSuchElementException:
            description = "No description available"

        results.append((url, title, description, index + 1))

    driver.quit()
    return results

def scrape_data(url, ua):
    try:
        response = requests.get(url, headers={'User-Agent': ua.random})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            headers = []
            for i in range(1, 7):
                for header in soup.find_all(f'h{i}'):
                    headers.append((f'<h{i}>', header.text))
            word_count = len(soup.get_text().split())
            return '', headers, word_count
        else:
            return f'Error {response.status_code}', [], 0
    except Exception as e:
        return str(e), [], 0

def format_headers(headers, indent=0):
    result = []
    for header in headers:
        result.append(" " * indent + f"{header['tag']} {header['text']}")
        result.extend(format_headers(header["children"], indent + 2))
    return result

def save_to_csv_and_txt(data, query, num_results, lang):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'serp_{query}_{num_results}_{lang}_{timestamp}.csv'
    txt_filename = f'serp_{query}_{num_results}_{lang}_{timestamp}.txt'

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile, open(txt_filename, 'w', encoding='utf-8') as txtfile:
        fieldnames = ['URL', 'Title', 'Description', 'Position', 'Error', 'Headers', 'Word_Count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for url, title, description, position, error, headers, word_count in data:
            formatted_headers = '\n'.join(f'{tag} {text}' for tag, text in headers)
            writer.writerow({'URL': url, 'Title': title, 'Description': description, 'Position': position, 'Error': error, 'Headers': formatted_headers, 'Word_Count': word_count})
            txtfile.write(f'URL: {url}\nTitle: {title}\nDescription: {description}\nPosition: {position}\nError: {error}\nHeaders:\n{formatted_headers}\nWord_Count: {word_count}\n\n{"-" * 80}\n\n')

    print(f"Data saved to {csv_filename} and {txt_filename}")


def main():
    query = input("Enter the search query: ")
    num_results = int(input("Enter the number of search results: "))
    lang = input("Enter the two-letter language code (e.g., 'en' for English): ")

    ua = UserAgent()

    search_results = search_google(query, num_results, lang, ua)

    if search_results:
        scraped_data = [(url, title, description, position, *scrape_data(url, ua)) for url, title, description, position in search_results]
        save_to_csv_and_txt(scraped_data, query, num_results, lang)
    else:
        print("No search results found.")

if __name__ == "__main__":
    main()

