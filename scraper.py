import io
import multiprocessing
import requests
import time
from datetime import date, datetime

import pandas as pd
import tqdm
from bs4 import BeautifulSoup
from pypdf import PdfReader


def _fetch_page_content(page_num=1, connect_reties=3):
  url = f"https://www.b3.com.br/pt_br/regulacao/oficios-e-comunicados/?pagination={page_num}"

  try:
    response = requests.get(url)
  except Exception as e:
    raise e

  return BeautifulSoup(response.text, 'html.parser')


def _get_pdf_content(url):
  return requests.get(url)


def scrape_b3(page_num):
  soup = _fetch_page_content(page_num)
  content_divs = soup.select('li.accordion-navigation')

  base_url = "https://www.b3.com.br"
  data = []

  for content in content_divs:
    published_date = content.select("div.least-content")[0].text
    published_title = content.select("div.content p.primary-text")[0].text
    published_abstract = content.select("div.content p.resumo-oficio")[0].text
    published_subject = content.select("div.content p.assunto-oficio")[0].text
    href = content.select("div.content ul li a")[0].get("href", None)

    url = base_url + href
    
    pdf_response = _get_pdf_content(url)
    pdf_bytes = pdf_response.content
    pdf_file = io.BytesIO(pdf_bytes)

    reader = PdfReader(pdf_file)
    pages = reader.pages
    full_text = ""
    for page in pages:
      full_text = full_text + page.extract_text()

    data.append([published_date, published_title, published_abstract, published_subject, url, full_text])

  return pd.DataFrame(data, columns=["published_date", "published_title", "published_abstract", "published_subject", "url", "full_text"])


if __name__ == "__main__":
    num_processes = 8
    pagination = [i for i in range(1, 275)] # There are 274 pages

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = list(
            tqdm.tqdm(
            pool.imap(scrape_b3, pagination),
            total=len(pagination)
            )
        )
    df = pd.concat(results)
    df.to_csv("results.csv")