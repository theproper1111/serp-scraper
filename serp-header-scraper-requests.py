import requests
from bs4 import BeautifulSoup
import csv
import uuid
from fake_useragent import UserAgent
import re
from googlesearch import search
import requests.exceptions
import time

def search_google(query, num_results, lang):
    results = []
    try:
        for url in search(query, num_results=num_results, lang=lang):
            try:
                ua = UserAgent()
                headers = {"User-Agent": ua.random}
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.find("title").text
                description = soup.find("meta", attrs={"name": "description"})
                if description:
                    description = description["content"]
                else:
                    description = ""
                results.append((url, title, description, None))
                time.sleep(2)  # Add a 2-second delay between requests
            except Exception as e:
                print(f"Error while processing URL {url}: {e}")
                results.append((url, None, None, e))
    except requests.exceptions.HTTPError as e:
        print(f"Error while searching Google: {e}")
    return results


def scrape_data(url):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    headers = [{"tag": header.name, "text": header.text} for header in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]

    # Get the word count of the page
    page_text = soup.get_text()
    word_count = len(page_text.split())

    structured_headers = []
    stack = []
    for header in headers:
        tag_level = int(header["tag"][1])
        while stack and int(stack[-1]["tag"][1]) >= tag_level:
            stack.pop()
        current_level = {"tag": header["tag"], "text": header["text"], "children": []}
        if stack:
            stack[-1]["children"].append(current_level)
        else:
            structured_headers.append(current_level)

    return structured_headers, word_count



def format_headers(headers, indent=0):
    result = []
    for header in headers:
        result.append(" " * indent + f"{header['tag']} {header['text']}")
        result.extend(format_headers(header["children"], indent + 2))
    return result

def save_to_csv_and_txt(data, query, num_results, lang):
    # Remove any non-alphanumeric characters from the query
    sanitized_query = re.sub(r'\W+', '_', query)

    # Save to CSV
    csv_filename = f"{sanitized_query}-{num_results}-{lang}.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["URL", "Title", "Description", "Word Count", "Headers", "SERP Position", "Error"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for url, title, description, position, error, headers, word_count in data:
            if error is None:
                formatted_headers = "\n".join(format_headers(headers))
                writer.writerow({"URL": url, "Title": title, "Description": description, "Word Count": word_count, "Headers": formatted_headers, "SERP Position": position, "Error": ""})
            else:
                writer.writerow({"URL": url, "Title": "", "Description": "", "Word Count": "", "Headers": "", "SERP Position": position, "Error": error})

    # Save to Text File
    txt_filename = f"{sanitized_query}-{num_results}-{lang}.txt"
    with open(txt_filename, "w", encoding="utf-8") as txtfile:
        for url, title, description, position, error, headers, word_count in data:
            txtfile.write(f"URL: {url}\n")
            txtfile.write(f"SERP Position: {position}\n")
            if error is None:
                txtfile.write(f"Title: {title}\n")
                txtfile.write(f"Description: {description}\n")
                txtfile.write(f"Word Count: {word_count}\n")
                txtfile.write("Headers:\n")
                txtfile.write("\n".join(format_headers(headers)))
            else:
                txtfile.write(f"Error: {error}\n")
            txtfile.write("\n\n" + "=" * 80 + "\n\n")

def main():
    query = input("Enter the search query: ")
    num_results = int(input("Enter the number of search results: "))
    lang = input("Enter the two-letter language code (e.g., 'en' for English): ")

    search_results = search_google(query, num_results, lang)
    scraped_data = [(url, title, description, position, error, *scrape_data(url)) if error is None else (url, title, description, position, error, None, None) for url, title, description, position, error in search_results]
    save_to_csv_and_txt(scraped_data, query, num_results, lang)

if __name__ == "__main__":
    main()

