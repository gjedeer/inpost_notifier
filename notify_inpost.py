#!/usr/bin/env python3

import json
import os
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, text):
    #Establish SMTP Connection
    s = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT', 587)))

    #Start TLS based SMTP Session
    s.starttls()

    #Login Using Your Email ID & Password
    s.login(os.getenv('SMTP_LOGIN'), os.getenv('SMTP_PASSWORD'))

    #To Create Email Message in Proper Format
    msg = MIMEMultipart()

    #Setting Email Parameters
    msg['From'] = os.getenv('SMTP_FROM', os.getenv('SMTP_LOGIN'))
    msg['To'] = os.getenv('YOUR_EMAIL')
    msg['Subject'] = subject

    #Email Body Content
    message = text

    #Add Message To Email Body
    msg.attach(MIMEText(message, 'text'))

    #To Send the Email
    s.send_message(msg)

    #Terminating the SMTP Session
    s.quit()

def get_waiting_parcels():
    #p = subprocess.run(['inpost-cli', 'ls', '-f', 'json', '-s', 'ready_to_pickup'])
    p = subprocess.run(['inpost-cli', 'ls', '-f', 'json', '-s', 'ready_to_pickup'], capture_output=True, check=True)
    json_r = p.stdout.decode('utf8')
    return json.loads(json_r)
#    with open('inpost-cli-json.json') as f:
#        return json.load(f)

def gpg_get_key(key_id):
    keyserver = os.getenv('PGP_KEYSERVER', 'keys.gnupg.net')
    print("Start getkeys")
    cmd = 'gpg --list-keys %s || gpg --verbose --openpgp --keyserver %s --recv-keys %s' % (key_id, keyserver, key_id)
    print(cmd)
    os.system(cmd)

def gpg_encrypt(key_id, text):
    gpg_get_key(key_id)
    print("Starting encryption")
    p = subprocess.run(['gpg', '--recipient', key_id, '-a', '--encrypt', '--batch', '--trust-model', 'always'], input=text.encode('utf-8'), capture_output=True, check=True)
    return p.stdout.decode('utf8')

def send_emails_for_waiting_parcels():
    msg = ''
    parcels = get_waiting_parcels()
    for parcel in parcels:
        msg += "%s (do %s) - od %s - %s %s\n" % (
            parcel['openCode'],
            parcel['expiryDate'],
            parcel['senderName'],
            parcel['pickupPoint']['addressDetails']['street'],
            parcel['pickupPoint']['addressDetails']['buildingNumber'],
        )

    if len(parcels) > 0:
        pgp_key_id = os.getenv('YOUR_PGP_KEY_ID', None)
        if pgp_key_id:
            msg_text = gpg_encrypt(pgp_key_id, msg)
        else:
            msg_text = msg
        print("Starting sending email")
        send_email('Paczki do odbioru', msg_text)


if __name__ == '__main__':
    send_emails_for_waiting_parcels()
