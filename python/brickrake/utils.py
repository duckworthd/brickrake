"""
Utility methods
"""
import urllib
import urlparse

from bs4 import BeautifulSoup as BS


def beautiful_soup(url):
  """Fetch a web page and return its contents as parsed by Beautiful Soup"""
  return BS(urllib.urlopen(url).read())


def get_params(url):
  parsed = urlparse.urlparse(url)
  params = urlparse.parse_qs(parsed.query)
  return dict( (k, v[0]) for (k, v) in params.iteritems())
