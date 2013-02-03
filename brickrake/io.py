"""
Functions for loading/saving data
"""
import json
import os
import xml.etree.ElementTree as etree

import numpy as np
import pandas


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


def save_bsx(f, allocation):
  '''Save an allocation (brickrake.minimize output) as BSX file'''
  # merge all items with the same (item id, color id)
  allocation = pandas.DataFrame.from_records(allocation)
  group = allocation[['item_id', 'color_id', 'quantity']] \
      .groupby(['item_id', 'color_id'], as_index=False) \
      .aggregate(np.sum)

  inventory = etree.Element("Inventory")
  for (_, row) in group.T.iteritems():
    item = etree.SubElement(inventory, "Item")

    item_id = etree.SubElement(item, "ITEMID")
    item_id.text = str(row['item_id'])

    color_id = etree.SubElement(item, "COLOR")
    color_id.text = str(row['color_id'])

    minqty = etree.SubElement(item, "MINQTY")
    minqty.text = str(int(row['quantity']))

    itemtype = etree.SubElement(item, "ITEMTYPE")
    itemtype.text = "P"   # TODO this is a big assumption :(

  etree.ElementTree(inventory).write(f)
  return


def save_bsx_per_vendor(folder, solution):
  '''Save an allocation for each vendor as BSX files in a folder'''
  # make folder
  try:
    os.makedirs(folder)
  except OSError:
    pass

  # create XML
  allocation = pandas.DataFrame.from_records(solution['allocation'])
  for (store_id, group) in allocation.groupby('store_id'):
    fname = os.path.join(folder, str(store_id) + '.xml')
    save_bsx(open(fname, 'w'), [row.to_dict() for (_, row) in group.T.iteritems()])


def load_price_guide(f):
  """Load pricing output"""
  return json.load(f)


def save_price_guide(f, price_guide):
  """Save pricing output"""
  json.dump(price_guide, f, indent=2)


def load_store_metadata(f):
  """Load metadata associated with stores"""
  return json.load(f)


def save_store_metadata(f, metadata):
  """Save metadata associated with stores"""
  json.dump(metadata, f, indent=2)


def load_solution(f):
  """Load a set of buying recommendations"""
  return json.load(f)


def save_solution(f, solutions):
  """Save a set of buying recommendations"""
  json.dump(solutions, f, indent=2)
