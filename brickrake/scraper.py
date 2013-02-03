"""
Functions for scraping bricklink.com
"""
import re
import urllib

from bs4 import BeautifulSoup as BS

import color
import utils


def price_guide(item, allowed_stores=None):
  """Fetch pricing info for an item"""
  parts_left = item['Qty']
  results = []

  if (item['ItemTypeID'] == 'P' and 'stk0' in item['ItemID']) or \
      item['ItemTypeID'] == 'S' or \
      item['ItemTypeID'] == 'M':
    # a sticker sheet, a set, or a minifigure
    color_ids = [0]
  else:
    # a normal item
    color_ids = color.similar_to(item['ColorID'])

  for c in color_ids:
    # perform HTTP request
    parameters = {
        'itemType': item['ItemTypeID'],
        'itemNo': item['ItemID'],
        'itemSeq': 1,
        'colorId': c,
        'v': 'P',
        'priceGroup': 'Y',
        'prDec': 2
    }
    url = "http://www.bricklink.com/catalogPG.asp?" + urllib.urlencode(parameters)
    html = urllib.urlopen(url).read()

    # parse page
    page = BS(html)

    if len(page.find_all(text='Currently Available')) == 0:
      # not available in this color :(
      continue
    else:
      for td in page.find_all('td'):
        if td.find('a', recursive=False, href=re.compile('/store.asp')) is not None:
          # find the td element with a link to a store. Its siblings contain
          # the interesting bits like price and quantity available
          store_url = td.find('a')['href']
          store_id = int(utils.get_params(store_url)['sID'])
          quantity = int(td.next_sibling.text)
          cost_per_unit = float(re.findall('[0-9.]+', td.next_sibling.next_sibling.text)[0])

          if (allowed_stores is not None) and (not store_id in allowed_stores):
            continue

          results.append({
            'item_id': item['ItemID'],
            'wanted_color_id': item['ColorID'],
            'color_id': c,
            'store_url': 'http://www.bricklink.com' + store_url,
            'store_id': store_id,
            'quantity_available': quantity,
            'cost_per_unit': cost_per_unit
          })

          parts_left -= quantity

    if parts_left <= 0:
      # stop early, we've got everything we need
      return results

  return results


def store_info():
  """Fetch metadata for all stores

  Parameters
  ----------
  store_id : int or None
      store id code.  If none, get store info for ALL stores
  """
  browse_page = utils.beautiful_soup('http://www.bricklink.com/browse.asp')
  country_links = (
    browse_page
    .find(text='Stores:').parent.parent.next_sibling
    .find_all('a', href=re.compile('countryID'))
  )

  result = []

  for country_link in country_links:
    country_name = country_link.text
    country_id = utils.get_params(country_link['href'])['countryID']

    country_page = utils.beautiful_soup('http://www.bricklink.com' + country_link['href'])
    store_links = country_page.find_all('a', href=re.compile('store.asp'))

    for store_link in store_links:
      store_page = utils.beautiful_soup('http://www.bricklink.com' + '/' + store_link['href'])
      params = utils.get_params(store_page.find('frame', src=re.compile('^storeTop.asp'))['src'])

      store_name = params['storeName']
      store_id = params['uID']
      country_name = params['cn']
      country_id = params['c']
      seller_name = params['p_seller']
      feedback = params['p_feedback']

      entry = {
        'store_name': store_name,
        'store_id': int(store_id),
        'country_name': country_name,
        'country_id': country_id,
        'seller_name': seller_name,
        'feedback': int(feedback)
      }

      result.append(entry)

  return result
