# -*- coding: utf-8 -*-
import sys
reload(sys) # Reload does the trick!
sys.setdefaultencoding('UTF8')
import os
import re
import requests
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil.parser import parse

# Set up variables
entity_id = "E4210_WMBC_gov"
url = "https://www.wigan.gov.uk/Council/DataProtection-FOI-Stats/Spending-and-Finance-data.aspx"
errors = 0
# Set up functions
def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    year, month = int(date[:4]), int(date[5:7])
    now = datetime.now()
    validYear = (2000 <= year <= now.year)
    validMonth = (1 <= month <= 12)
    if all([validName, validYear, validMonth]):
        return True
def validateURL(url):
    try:
        r = requests.get(url, allow_redirects=True)
        return r.status_code == 200
    except:
        raise
def validateFiletype(url):
    try:
        r = requests.head(url, allow_redirects=True)
        sourceFilename = r.headers.get('Content-Disposition')

        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        elif r.headers['Content-Type'] == 'text/csv':
            ext = '.csv'
        else:
            ext = os.path.splitext(url)[1]

        if ext in ['.csv', '.xls', '.xlsx']:
            return True
    except:
        raise
def convert_mth_strings ( mth_string ):

    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    #loop through the months in our dictionary
    for k, v in month_numbers.items():
#then replace the word with the number

        mth_string = mth_string.replace(k, v)
    return mth_string
# pull down the content from the webpage
html = urllib2.urlopen(url)
soup = BeautifulSoup(html, 'lxml')
# find all entries with the required class
block = soup.find('div', attrs = {'id':'L3_MainContentPlaceholder'}).find_all_next('ul')
for b in block:
    links = b.find_all('a')
    for link in links:
        if 'Spend' in link.text:
            if '.csv' in link['href']:
                url = 'https://www.wigan.gov.uk' + link['href']
                csvMth = link.text.strip().split('-')[-1].strip().split('(')[0].strip()[:3]
                csvYr = link.text.strip().split('-')[-1].strip().split('(')[0].strip()[-4:]
                csvMth = convert_mth_strings(csvMth.upper())
                if len(link.text.split('-')) > 2:
                    filename = 'Q'+entity_id + "_" + csvYr + "_" + csvMth
                else:
                    filename = entity_id + "_" + csvYr + "_" + csvMth
                todays_date = str(datetime.now())
                file_url = url.strip()
                if not validateFilename(filename):
                    print filename, "*Error: Invalid filename*"
                    print file_url
                    errors += 1
                    continue
                if not validateURL(file_url):
                    print filename, "*Error: Invalid URL*"
                    print file_url
                    errors += 1
                    continue
                if not validateFiletype(file_url):
                    print filename, "*Error: Invalid filetype*"
                    print file_url
                    errors += 1
                    continue
                scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
                print filename

if errors > 0:
   raise Exception("%d errors occurred during scrape." % errors)
