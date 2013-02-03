"""
Algorithms for minimizing cost of a purchase
"""
import itertools

import numpy as np
import pandas


def brute_force(wanted_parts, price_guide, k):
  """Enumerate all possible combinations of k stores"""
  stores = set(e['store_id'] for e in price_guide)
  results = []
  for selected_stores in itertools.combinations(stores, k):
    # get items sold by these stores only
    inventory = filter(lambda x: x['store_id'] in selected_stores, price_guide)
    if covers(wanted_parts, inventory):
      # calculate minimum cost to buy everything using these stores
      cost, allocation = min_cost(
        wanted_parts,
        filter(lambda x: x['store_id'] in selected_stores, price_guide)
      )
      results.append({
        'cost': cost,
        'allocation': allocation,
        'store_ids': selected_stores
      })
      print 'Solution: k=%d, cost=%8.2f, store_ids=%40s' % (k, cost, selected_stores)
  return results


#def min_cost(wanted_parts, available_parts):
#  """Find the lowest cost way to buy all wanted_parts"""
#  result = []
#  wanted_parts = pandas.DataFrame.from_records(wanted_parts)
#  available_parts = pandas.DataFrame.from_records(available_parts)
#  groups = available_parts.groupby(['item_id', 'wanted_color_id'])
#  for ((item_id, wanted_color_id), group) in groups:
#    group = group.sort('cost_per_unit')
#    items = wanted_parts[
#        (wanted_parts['ItemID'] == item_id)
#        & (wanted_parts['ColorID'] == wanted_color_id)
#    ]
#
#    if items.shape[0] == 0
#      continue
#    else:
#      item = items.irow(0)
#
#    n_remaining = item['Qty']
#    for (_, row) in group.T.iteritems():
#      if n_remaining <= 0:
#        break
#      amount = min(n_remaining, row['quantity_available'])
#      r = {
#        'item_id': row['item_id'],
#        'color_id': row['color_id'],
#        'store_id': row['store_id'],
#        'quantity': amount,
#        'cost_per_unit': row['cost_per_unit']
#      }
#      result.append(r)
#      n_remaining -= amount
#
#    if n_remaining > 0:
#      print 'WARNING: couldn\'t find enough %s %s' % (item['ColorName'], item['ItemName'])
#
#  cost = sum([e['quantity'] * e['cost_per_unit'] for e in result])
#  return (cost, result)

def min_cost(wanted_parts, available_parts):
  """Find the lowest cost way to buy all wanted_parts"""
  result = []
  for item in wanted_parts:
    # filter available_parts for inventory that match this item
    def f(x):
      return (
        x['wanted_color_id'] == item['ColorID']
        and x['item_id'] == item['ItemID']
      )
    matching = list(sorted(filter(f, available_parts),
                           key = lambda x: -1 * x['cost_per_unit']))

    # take as much inventory as possible, starting with the lowest price, until
    # the requested quantity is filled
    n_remaining = item['Qty']
    while n_remaining > 0:
      if len(matching) == 0:
        print 'WARNING: couldn\'t find enough inventory to purchase %s' % (item['ItemName'],)
        break
      next = matching.pop()
      amount = min(n_remaining, next['quantity_available'])
      r = {
        'item_id': next['item_id'],
        'color_id': next['color_id'],
        'store_id': next['store_id'],
        'quantity': amount,
        'cost_per_unit': next['cost_per_unit']
      }
      result.append(r)
      n_remaining -= amount

  cost = sum([e['quantity'] * e['cost_per_unit'] for e in result])
  return (cost, result)


#def covers(wanted_parts, available_parts):
#  """True if the given stores can cover all desired items"""
#  available_parts = pandas.DataFrame.from_records(available_parts)
#  available_parts = available_parts[
#      ['item_id', 'wanted_color_id', 'quantity_available']
#    ] \
#      .groupby(['item_id', 'wanted_color_id'], as_index=False) \
#      .aggregate(np.sum)
#
#  wanted_parts = pandas.DataFrame.from_records(wanted_parts)
#  wanted_parts = wanted_parts[
#      ['ItemID', 'ColorID', 'Qty']
#  ]
#  together = pandas.merge(
#      wanted_parts, available_parts,
#      left_on=['ItemID', 'ColorID'], right_on=['item_id', 'wanted_color_id'],
#      how='left'
#  )
#  together = together.fillna(0)
#  return np.all(together['Qty'] <= together['quantity_available'])


def covers(wanted_parts, available_parts):
  """True if the given stores can cover all desired items"""
  for item in wanted_parts:
    # filter available_parts for inventory that match this item
    def f(x):
      return (
        x['wanted_color_id'] == item['ColorID']
        and x['item_id'] == item['ItemID']
      )
    matching = list(sorted(filter(f, available_parts),
                           key = lambda x: -1 * x['cost_per_unit']))
    total_available = sum(e['quantity_available'] for e in matching)
    if total_available < item['Qty']:
      return False
  return True


# TODO this doesn't work at all
#def greedy(wanted_parts, price_guide):
#  """Greedily select stores that cover the most items"""
#  price_guide = pandas.DataFrame.from_records(price_guide)
#  wanted_parts = pandas.DataFrame.from_records(wanted_parts)
#  remaining_parts = wanted_parts.copy()
#
#  store_ids = []
#  while not covers(wanted_parts, store_ids, price_guide):
#    coverage = []
#    for store_id in set(price_guide['store_id']):
#      # only items from this store
#      from_this_store = price_guide[price_guide['store_id'] == store_id]
#
#      # match them together
#      together = pandas.merge(remaining_parts, from_this_store,
#        left_on=['ItemTypeID', 'ColorID'], right_on=['item_id', 'wanted_color_id'],
#        how='inner'
#      )
#
#      # find out how many pieces I'd end up buying from this store
#      quantities = np.min([together['quantity_available'], together['Qty']], axis='???')
#
#      # save that number and the store id
#      coverage.append( (np.sum(quantities), store_id) )
#
#    # use the store that covers the most of my wanted list
#    most_covering = list(sorted(coverage))[-1][1]
#    store_ids.append(most_covering)
#
#    # remove everything I can buy from this store from the remaining parts list
