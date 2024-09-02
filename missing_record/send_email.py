"""Send an email with the given html content."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

import yaml
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Get the email credentials
EMAIL_SERVER = os.getenv("EMAIL_SERVER")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")


def send_email(recipient, subject, html_content):
    """Send an email with the given html content."""
    # Create a multipart message
    msg = MIMEMultipart("alternative")
    # Set the sender and recipient
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject
    # Read the html file

    msg.attach(MIMEText(html_content, "html"))

    # Connect to the SMTP server using STARTTLS
    with smtplib.SMTP(EMAIL_SERVER, 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
    print(f"Sent to {recipient}, next email sending in 12 seconds...")
    time.sleep(12)


def send():
    with open("config_files/recipients.yaml") as file:
        sending_list = yaml.safe_load(file)

    for recipient in sending_list:
        html_content = (
            "<p>This is a test of the missing record report v2</p>"
            "<p>I improved the rainfall section</p>"
            "<p>Now doesn't report as missing unless it is missing data for 2 hours</p>"
            "<p>So should be working for sites which return hourly zeroes</p>"
            "<p>Will still over-report dry sites which only give a 6am value</p>"
            "<p>This can be viewed with colours at:"
            r"<p>\\ares\Hydrology\Hydrology Regions\Missing Record Reporting</p>"
        )
        for suffix in sending_list[recipient]["file_suffix"]:
            with open(f"output_html/output{suffix}.html") as html_file:
                html_content += html_file.read()
        for address in os.getenv(recipient).split(","):
            print(address)
            send_email(address, sending_list[recipient]["title"], html_content)
    print("Email(s) sent successfully!")


if __name__ == "__main__":
    send()
