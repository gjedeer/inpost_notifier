#!/usr/bin/env python3

import json
import os
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase


def send_email(subject, text):
    #Establish SMTP Connection
    s = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT', 587)))

    #Start TLS based SMTP Session
    s.starttls()

    #Login Using Your Email ID & Password
    s.login(os.getenv('SMTP_LOGIN'), os.getenv('SMTP_PASSWORD'))

    #To Create Email Message in Proper Format
    msg = MIMEText(text)

    #Setting Email Parameters
    msg['From'] = os.getenv('SMTP_FROM', os.getenv('SMTP_LOGIN'))
    msg['To'] = os.getenv('YOUR_EMAIL')
    msg['Subject'] = subject

    #To Send the Email
    s.sendmail(msg['From'], [msg['To']], msg.as_string())

    #Terminating the SMTP Session
    s.quit()

def get_waiting_parcels():
    if os.getenv('TEST_DATA', False):
        with open('inpost-cli-json.json') as f:
            return json.load(f)
    else:
        p = subprocess.run(['inpost-cli', 'ls', '-f', 'json', '-s', 'ready_to_pickup'], capture_output=True, check=True)
        json_r = p.stdout.decode('utf8')
        return json.loads(json_r)

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

def get_parcels_state_path():
    return os.getenv('PARCEL_STATE_PATH', os.path.expanduser('~/.config/alufers/inpost-cli/notifications_sent.txt'))

def new_parcels_present(numbers):
    numbers_found = set()
    if not os.path.exists(get_parcels_state_path()):
        return True
    with open(get_parcels_state_path()) as f:
        for line_ in f:
            line = line_.strip()
            for number in numbers:
                if number == line:
                    numbers_found.add(number)
            
    return set(numbers) - numbers_found

def store_notified_parcels(numbers):
    new_parcels = new_parcels_present(numbers)
    with open(get_parcels_state_path(), 'a') as f:
        for number in numbers:
            f.write(number.strip() + '\n')

def send_emails_for_waiting_parcels():
    msg = ''
    parcels = get_waiting_parcels()
    parcel_numbers = [parcel['shipmentNumber'] for parcel in parcels]

    if not new_parcels_present(parcel_numbers):
        print("No new parcels present, exiting")
        return

    pickup_points = set([ (
        parcel['pickupPoint']['addressDetails']['street'], 
        parcel['pickupPoint']['addressDetails']['buildingNumber'], 
        parcel['pickupPoint']['name'],
        parcel['phoneNumber']
    ) for parcel in parcels])
    for pickup_point in pickup_points:
        msg += "%s %s (%s) tel %s:\n" % pickup_point
        for parcel in parcels:
            parcel_pickup = (
                parcel['pickupPoint']['addressDetails']['street'], 
                parcel['pickupPoint']['addressDetails']['buildingNumber'], 
                parcel['pickupPoint']['name'],
                parcel['phoneNumber']
            )
            if parcel_pickup != pickup_point:
                continue
            msg += "%s %s (do %s) - od %s\n" % (
                parcel['openCode'][:3],
                parcel['openCode'][3:],
                parcel['expiryDate'],
                parcel['senderName'],
            )

    if len(parcels) > 0:
        pgp_key_id = os.getenv('YOUR_PGP_KEY_ID', None)
        if pgp_key_id:
            msg_text = gpg_encrypt(pgp_key_id, msg)
        else:
            msg_text = msg
        print("Starting sending email")
        send_email('Paczki do odbioru', msg_text)
        store_notified_parcels(parcel_numbers)


if __name__ == '__main__':
    send_emails_for_waiting_parcels()
