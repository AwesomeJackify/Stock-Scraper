#!/usr/bin/env python3

"""
Update my stock spreadsheet
"""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Web scraping
import requests
from bs4 import BeautifulSoup

import re
import pprint
import datetime

import sys

# Constants
TICKER = sys.argv[1].upper()
DATE = None

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1D_IO1APspGn-vIc-vvz9EWsdW2TQtVBfvJ2xQgLo6-A'
RANGE_NAME = 'Multiday Breakout!A3:X3'

columns = {}

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        return

def set_date():
    date = sys.argv[2]
    date_split = date.split('-')
    date_formated = datetime.datetime(int(date_split[2]), int(date_split[1]), int(date_split[0]))
    global DATE
    DATE = date_formated.strftime('%b %d, %Y')

def check_url(url):
    try:
        r = requests.get(url)
        return r.content
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

def get_data(url, target):
    checked_url = check_url(url)
    html = BeautifulSoup(checked_url, 'html.parser')
    # Remove new lines
    html_cleanup = str(html).replace('\n', '')

    if (target == "category"):
        # Get category
        regex = re.search('industry":"([\s\S]*?)"', str(html_cleanup))
        columns['category'] = regex.group(1)
    elif (target == 'statistics'):
        # Get market cap
        regex = re.search('marketCap":{"\w+":\d+,"\w+":"(\d+\.\d+)M"', html_cleanup)
        columns['market cap'] = regex.group(1)

        # Get float
        regex = re.search('floatShares":{"\w+":\d+,"f\w+":"(\d+\.\d+)M"', html_cleanup)
        columns['float'] = regex.group(1)
    elif (target == 'historical'):
        date_td = html.find('td', text = DATE)
        date_td_siblings = list(date_td.next_siblings)

        # Get prices
        for i in range(4):
            if i == 0:
                columns['open'] = date_td_siblings[i].text
            elif i == 1:
                columns['high'] = date_td_siblings[i].text
            elif i == 2:
                columns['low'] = date_td_siblings[i].text
            elif i == 3:
                columns['close'] = date_td_siblings[i].text

if __name__ == '__main__':
    main()
    set_date()

    home_url = 'https://finance.yahoo.com/quote/' + TICKER
    statistics_url = 'https://finance.yahoo.com/quote/' + TICKER + '/key-statistics'
    historical_url = 'https://finance.yahoo.com/quote/' + TICKER + '/history'

    get_data(home_url, 'category')
    get_data(statistics_url, 'statistics')
    get_data(historical_url, 'historical')

    values = [
        [

        ],
    ]
    body = {
        'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
        valueInputOption='RAW', body=body).execute()
    print('{0} cells appended.'.format(result \
                                           .get('updates') \
                                           .get('updatedCells')))
