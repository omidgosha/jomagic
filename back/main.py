import threading
import time
import smtplib
import os
import pymongo
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, request, jsonify
import PyPDF2

app = Flask(__name__)

# MongoDB configuration
MONGO_CONNECTION_STRING = "mongodb://localhost:27017/"
MONGO_DB_NAME = "pdf_database"
MONGO_COLLECTION_NAME = "pdf_files"

# Replace these with your actual email credentials
SMTP_SERVER = 'smtp.example.com'
SMTP_PORT = 587
EMAIL_USERNAME = 'your_email@example.com'
EMAIL_PASSWORD = 'your_email_password'

def send_email(recipient, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USERNAME
    msg['To'] = recipient

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, [recipient], msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def find_pdf_file(name, date):
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]

    query = {"name": {"$regex": name}, "date": date}
    result = collection.find_one(query)

    if result:
        return result["file_path"]
    else:
        return None

def search_pdf_file(name, date):
    # file_path = find_pdf_file(name, date)
    # if not file_path:
    #     return jsonify({"error": "File not found"}), 404

    # Search for the name in the PDF file
    with open('/Users/omid_ch/Documents/Development/JournalOfficiel/back/jos/jo12072023.pdf', 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)

        for page_number in range(num_pages):
            page = pdf_reader.pages[page_number]
            pagecontent = page.extract_text();
            if page_number == 1:
                print(pagecontent)
                print('name: '+ name)
            if name in pagecontent:
                return jsonify({"page_number": page_number + 1})
            if name.upper() in pagecontent:
                return jsonify({"page_number": page_number + 1})
            if name.lower() in pagecontent:
                return jsonify({"page_number": page_number + 1})

    return jsonify({"error": "Name not found in the PDF file"}), 404

def scrape_website():
    # Create a WebDriver (using Chrome here, but you can choose another supported browser)
    driver = webdriver.Chrome()

    try:
        # Go to the website X
        driver.get("https://www.example.com/")  # Replace with the actual URL of the website

        # Find the <a> tag with innerHTML containing "Extrait du Journal"
        link_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Extrait du Journal')]"))
        )

        # Click on the link if it's found
        link_element.click()

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Close the WebDriver after the task is finished
        driver.quit()

def run_scraping_thread():
    # Get the current date and time
    now = time.localtime()
    current_hour = now.tm_hour
    current_minute = now.tm_min

    # Set the time for the first run (9 am)
    target_hour = 9
    target_minute = 0

    # Calculate the time to the first run
    time_diff_seconds = (target_hour - current_hour) * 3600 + (target_minute - current_minute) * 60

    # If the target time has already passed for today, schedule it for the next day
    if time_diff_seconds < 0:
        time_diff_seconds += 24 * 3600

    # Sleep until the first run time
    time.sleep(time_diff_seconds)

    # Run the scraping thread every 24 hours
    while True:
        scrape_website()
        # Sleep for 24 hours before running the thread again
        time.sleep(24 * 3600)

# Start the scraping thread on server startup
scraping_thread = threading.Thread(target=run_scraping_thread)
scraping_thread.start()

# Define the "search" endpoint
@app.route("/search", methods=["GET", "POST"])
def search_endpoint():
    name = request.args.get("name")
    date = request.args.get("date")

    if not name or not date:
        return jsonify({"error": "Both 'name' and 'date' parameters are required"}), 400

    return search_pdf_file(name, date)

if __name__ == "__main__":
    app.run(debug=True)
