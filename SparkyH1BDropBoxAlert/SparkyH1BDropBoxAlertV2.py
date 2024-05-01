from telethon.sync import TelegramClient
import datetime
import pandas as pd
import configparser
import smtplib
from email.mime.text import MIMEText
import time  # Needed for sleep
import json
import requests
import pytz

# Define the send_email function
def send_email(body, smtp_username, smtp_password):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    email = MIMEText(body)
    email['From'] = smtp_username
    email['To'] = smtp_username  # Consider adding a more specific recipient here
    email['Subject'] = '[URGENT-R] Jul Aug Slot Available'
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    # Send to self
    server.sendmail(smtp_username, [smtp_username], email.as_string())
    # Send to IFTTT  -- Use this to alert in your phone via IFFT App notification
    # server.sendmail(smtp_username, ['trigger@applet.ifttt.com'], email.as_string())
    server.quit()

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')
smtp_username = config['SMTP']['username']
smtp_password = config['SMTP']['password']
api_id = config['TELEGRAM']['r_api_id']
api_hash = config['TELEGRAM']['r_api_hash']

# Define your timezone
est = pytz.timezone('America/New_York')

print(api_id)
print(api_hash)

#chats = ['@H1B_H4_Visa_Dropbox_Slots']
#chats = ['@us_visa_stamping_india', '@h1bh4_dropbox_visa_slots', '@h1bh4chennai', 'StrictlyH1_H4_regular_visa_slots']
chats = ['H1B_H4_Visa_Dropbox_slots', 'us_visa_stamping_india', 'h1bh4_dropbox_visa_slots', 'h1bh4chennai', 'StrictlyH1_H4_regular_visa_slots']

# Main loop
while True:
    client = TelegramClient('new_session_name', api_id, api_hash)
    client.start()

    data_list = []
   
    utc_now = datetime.datetime.now(pytz.utc)
    sixty_seconds_ago_utc = utc_now - datetime.timedelta(minutes=1)
    #sixty_seconds_ago_utc = utc_now - datetime.timedelta(minutes=1)

    for chat in chats:
        for message in client.iter_messages(chat, offset_date=sixty_seconds_ago_utc, reverse=True):
            message_date_est = message.date.astimezone(est)
            data = {
                "group": chat,
                "sender": message.sender_id,
                "text": message.text,
                "date": message_date_est  # Now in EST
            }
            data_list.append(data)

    df = pd.DataFrame(data_list)

    # Save all fetched messages to CSV before filtering
    if not df.empty:
        print("Found Messages")
        df.to_csv('messages.csv', index=False)
        
        if 'date' in df.columns:
            df['date'] = df['date'].dt.tz_localize(None)
        if 'text' in df.columns:
            df['text_lower'] = df['text'].str.lower()            
            #customization this code to include what word you need to get alert
            pattern_include = r'(jul|aug)\s*(\d+|all)?'
            #customization this code to exclude what word you need to get alert
            pattern_exclude = r'n/?a|not available|not there|na|n.a'
            filtered_include = df[df['text_lower'].str.contains(pattern_include, case=False, regex=True, na=False)]
            #final_df = filtered_include[~filtered_include['text_lower'].str.contains(pattern_exclude, case=False, regex=True, na=False)]
            final_df = filtered_include
            final_df.to_csv('filtered_messages.csv', columns=['text'], index=False)
            
            if final_df.empty:
                print("Did not pass filter criteria. Skipping email!!")

            if not final_df.empty:
                body = '\n'.join(f"{row['date']} - {row['text']}" for _, row in final_df.iterrows())
                print("reached email block")
                send_email(body, smtp_username, smtp_password)
        else:
            print("No 'text' column found in DataFrame. This likely means no messages were fetched.")
    else:
        print("DataFrame is empty. No messages were fetched.")

    client.disconnect()
    time.sleep(30)
