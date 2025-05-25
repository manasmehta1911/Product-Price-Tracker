import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time

# === CONFIGURATION ===
URL = "http://books.toscrape.com/catalogue/category/books_1/index.html"
PRICE_THRESHOLD = 30.00  # Send alert if price drops below this
SMTP_SERVER = 'smtp.zoho.in'
SMTP_PORT = 465
EMAIL_SENDER = 'manasproject1911@zohomail.in'           # <-- Your Zoho email
EMAIL_PASSWORD = 'infotact'           # <-- Your Zoho app password (not account password)
EMAIL_RECEIVER = 'manasproject1911@gmail.com'        # <-- Receiver email for alerts

# === SCRAPER FUNCTION ===
def scrape_books():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    books = []
    for article in soup.select('article.product_pod'):
        title = article.h3.a['title']
        price_str = article.select_one('p.price_color').text.strip().replace('Â', '').replace('£', '')
        try:
            price = float(price_str)
        except ValueError:
            continue
        book_url = article.h3.a['href']
        full_url = f"http://books.toscrape.com/catalogue/{book_url}"
        books.append({'title': title, 'price': price, 'url': full_url})
    return books

# === EMAIL ALERT FUNCTION ===
def send_email_alert(cheap_books):
    subject = f"{len(cheap_books)} Books Below £{PRICE_THRESHOLD}"
    body = "The following books are on sale:\n\n"
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

# === MAIN CHECK FUNCTION ===
def check_prices():
    print("Checking book prices")
    books = scrape_books()
    cheap_books = [b for b in books if b['price'] < PRICE_THRESHOLD]
    if cheap_books:
        print(f"Found {len(cheap_books)} books below £{PRICE_THRESHOLD}")
        send_email_alert(cheap_books)
    else:
        print(" No books found below threshold.")

# === SCHEDULER SETUP ===
schedule.every(12).hours.do(check_prices)

if __name__ == "__main__":
    print("Book Price Alert started. Monitoring every 12 hours...")
    check_prices()  # Run once at start
    while True:
        schedule.run_pending()
        time.sleep(60)
