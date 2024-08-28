"""Send an email with the given html content."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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


if __name__ == "__main__":
    sending_list = {
        "CENTRAL_RECIPIENTS": [
            "Hi fake Paul, please tell Sam you got central's report",
            "_Central",
        ],
        "EASTERN_RECIPIENTS": [
            "Hi fake Tane, please tell Sam you got eastern's report",
            "_Eastern",
        ],
        "NORTHERN_RECIPIENTS": [
            "Hi fake Nathan, please tell Sam you got northern's report",
            "_Northern",
        ],
        "SPECIAL_RECIPIENTS": [
            "Hi fake Brownie, please tell Sam you got special's report",
            "_Special",
        ],
    }
    subject = "TESTING THE Missing Values Report"
    with open("output_dump/output.html") as html_file:
        html_content = html_file.read()

    for recipients in sending_list:
        for recipient in recipients.split(","):
            print(os.getenv(recipient))
            with open(
                f"output_dump/output{sending_list[recipient][1]}.html"
            ) as html_file:
                html_content = html_file.read()
            send_email(os.getenv(recipient), sending_list[recipient][0], html_content)
    print("Email(s) sent successfully!")
