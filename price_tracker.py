import json
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time

# === LOAD CONFIG ===
with open('config.json') as f:
    config = json.load(f)

EMAIL_SENDER = config["email_sender"]
EMAIL_PASSWORD = config["email_password"]
EMAIL_RECEIVER = config["email_receiver"]
PRICE_THRESHOLD = config["price_threshold"]
SMTP_SERVER = config["smtp_server"]
SMTP_PORT = config["smtp_port"]

BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"

# === SCRAPE ALL BOOKS ===
def scrape_all_books():
    books = []
    page = 1
    while True:
        url = BASE_URL.format(page)
        print(f"Scraping page {page}")
        response = requests.get(url)
        if response.status_code != 200:
            break  # No more pages
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.select('article.product_pod')
        if not articles:
            break
        for article in articles:
            title = article.h3.a['title']
            price_str = article.select_one('p.price_color').text.strip().replace('Â', '').replace('£', '')
            try:
                price = float(price_str)
            except ValueError:
                continue
            partial_url = article.h3.a['href']
            full_url = f"http://books.toscrape.com/catalogue/{partial_url}"
            books.append({'title': title, 'price': price, 'url': full_url})
        page += 1
    return books

# === EMAIL ALERT ===
def send_email_alert(cheap_books):
    subject = f"{len(cheap_books)} Books Below £{PRICE_THRESHOLD}"
    body = "The following books are below your price threshold:\n\n"
    for book in cheap_books:
        body += f"{book['title']} - £{book['price']}\n{book['url']}\n\n"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email sent via Zoho Mail!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# === PRICE CHECK ===
def check_prices():
    print("Checking book prices")
    books = scrape_all_books()
    cheap_books = [b for b in books if b['price'] < PRICE_THRESHOLD]
    if cheap_books:
        print(f"Found {len(cheap_books)} books below £{PRICE_THRESHOLD}")
        send_email_alert(cheap_books)
    else:
        print("No books found below threshold.")

# === SCHEDULER SETUP ===
schedule.every(12).hours.do(check_prices)

if __name__ == "__main__":
    print("Book Price Alert started using config.json")
    check_prices()  # Run once at start
    while True:
        schedule.run_pending()
        time.sleep(60)
