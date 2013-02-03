"""
Functions for loading/saving data
"""
import json
import xml.etree.ElementTree as etree


# conversion functions for specific fields in a BSX file
CONVERT = {
  'Qty': int,
  'Price': float,
  'OrigPrice': float,
  'OrigQty': int,
  'ColorID': int,
}

def load_bsx(f):
  """Parse all items from a Brickstore Parts List XML file (*.bsx)

  Parameters
  ----------
  f : file-like object
      file containing XML contents"""
  root = etree.parse(f)
  items = []
  for item in root.findall('//Inventory/Item'):
    item_dict = {}
    for child in item.getchildren():
      tag = child.tag
      value = CONVERT.get(child.tag, lambda x: x)(child.text)
      item_dict[tag] = value
    items.append(item_dict)
  return items


def load_price_guide(f):
  """Load pricing output"""
  return json.load(f)


def save_price_guide(f, price_guide):
  """Save pricing output"""
  json.dump(price_guide, f, indent=2)


def load_store_metadata(f):
  """Load metadata associated with stores"""
  return json.load(f)


def save_solutions(path, metadata):
  """Save a set of buying recommendations"""
  json.dump(metadata, f, indent=2)


def load_solutions(f):
  """Load a set of buying recommendations"""
  return json.load(f)


def save_store_metadata(path, metadata):
  """Save metadata associated with stores"""
  json.dump(metadata, f, indent=2)
