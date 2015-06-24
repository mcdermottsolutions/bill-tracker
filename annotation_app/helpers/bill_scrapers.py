from urllib import request
import re, xmltodict
from bs4 import BeautifulSoup


# initial_data format:
# {'session': '84R', 'chamber_origin': 'S', 'number': '5'}

def scrape_bill_text(initial_data):
  ### Helper functions
  # ftpopen is not 100% reliable on first try
  def keep_trying_ftpopen(url, tries=7):
    # TODO: figure out optimal number of 'tries'

    # One last try, allow exception
    if tries <= 1:
      with request.urlopen(url) as response:
        return response.read()

    try:
      with request.urlopen(url) as response:
        return response.read()
    except:
      return keep_trying_ftpopen(url, tries=tries-1)

  ### Implementation proper
  bill_data = initial_data

  # example full URL:
  # 'ftp://ftp.legis.state.tx.us/bills/84R/billhistory/senate_bills/SB00001_SB00099/SB 10.xml'
  # bill_hist_file_url_unformatted = 'ftp://ftp.legis.state.tx.us/bills/' +\
  #   '{0}/billhistory/{1}_bills/{2}B{3}0{5}_{2}B{3}99/{2}B {4}.xml'

  # example full URL:
  # 'ftp://ftp.legis.state.tx.us/bills/833/billtext/HTML/house_bills/HB00001_HB00099/HB00010I.HTM'
  bill_text_files_url_unformatted = 'ftp://ftp.legis.state.tx.us/bills/' +\
    '{0}/billtext/HTML/{1}_bills/{2}B{3}0{4}_{2}B{3}99/'

  bill_text_filename_unformatted = '{0}B{1}\w.HTM$'

  # Are you looking for Senate Bills (SB) or House Bills (HB)?
  ch_abbr = bill_data['chamber_origin']
  if ch_abbr == 'S':
    chamber = 'senate'
  elif ch_abbr == 'H':
    chamber = 'house'

  # Get proper bill_hist_file_url & bill_text_file_url
  bill_number = str(bill_data['number'])
  if bill_data['number'] > 99:
    # bill_hist_file_url = bill_hist_file_url_unformatted.format(
    #   bill_data['session'], chamber, ch_abbr, bill_number[:-2].zfill(3),
    #   bill_number, 0)

    bill_text_files_url = bill_text_files_url_unformatted.format(
      bill_data['session'], chamber, ch_abbr, bill_number[:-2].zfill(3), 0)
  else:
    # bill_hist_file_url = bill_hist_file_url_unformatted.format(
    #   bill_data['session'], chamber, ch_abbr, '000', bill_number, 1)

    bill_text_files_url = bill_text_files_url_unformatted.format(
      bill_data['session'], chamber, ch_abbr, '000', 1)

  bill_text_filename_regex = bill_text_filename_unformatted.format(
    ch_abbr, bill_number.zfill(5))

  # Get XML data
  # response = str(keep_trying_ftpopen(bill_hist_file_url))
  # data = xmltodict.parse(response[14:-1])['billhistory']

  # Get only data I want
  # bill_data['caption'] = data['caption']['#text']
  # bill_data['history_url'] = bill_hist_file_url

  # Parse folder structure for latest version of bill_text
  response = str(keep_trying_ftpopen(bill_text_files_url))[2:]
  response = response.split('\\r\\n')[:-1]
  files = list(filter(lambda x: re.search(bill_text_filename_regex, x,
    re.IGNORECASE), response))

  from datetime import date
  def map_dates_and_filenames(text):
    matches = re.search('^(\d+)-(\d+)-(\d+).+' + '(' +\
      bill_text_filename_regex[:-1] + ')$', text, re.IGNORECASE)
    bill_date = date(year=int(matches.group(3))+2000,
      month=int(matches.group(1)), day=int(matches.group(2)))
    return [bill_date, matches.group(4)]

  # Wizardry to actually get the latest filename
  files = list(map(map_dates_and_filenames, files))
  bill_text_filename = max(files, key=lambda x: x[0])[1]

  # Get bill text (finally!)
  bill_text = keep_trying_ftpopen(bill_text_files_url + bill_text_filename)

  soup = BeautifulSoup(bill_text).find_all('table')[1].find_all('td')
  soup = list(filter(lambda x: not re.search('meta', str(x)), soup))
  soup = list(map(lambda x: x.get_text(), soup))
  print(''.join(soup[4:]))
  return

# input = {'session': '84R', 'chamber_origin': 'S', 'number': 5}
### Execution
# bill_scrape(input)

### Speed test
# from timeit import Timer
# t = Timer(lambda: bill_scrape(input))
# print(t.timeit(number=1))
