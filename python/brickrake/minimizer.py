"""
Algorithms for minimizing cost of a purchase
"""
import copy
import itertools

import numpy as np
import pandas

import utils


def brute_force(wanted_parts, price_guide, k):
  """Enumerate all possible combinations of k stores"""
  by_store = utils.groupby(price_guide, lambda x: x['store_id'])

  results = []
  for selected_stores in itertools.combinations(by_store.keys(), k):
    # get items sold by these stores only
    inventory = utils.flatten( by_store[s] for s in selected_stores )
    if covers(wanted_parts, inventory):
      # calculate minimum cost to buy everything using these stores
      cost, allocation = min_cost(wanted_parts, inventory)
      results.append({
        'cost': cost,
        'allocation': allocation,
        'store_ids': selected_stores
      })
      print 'Solution: k=%d, cost=%8.2f, store_ids=%40s' % (k, cost, selected_stores)
    else:
      #print 'Unable to fill quote using store_ids=%40s' % (selected_stores,)
      pass
  return results


def min_cost(wanted_parts, available_parts):
  """Find the lowest cost way to buy all wanted_parts"""
  kf = lambda x: (x['item_id'], x['wanted_color_id'])
  available_parts = utils.groupby(available_parts, kf)

  result = []
  cost = 0.0
  for item in wanted_parts:
    item_id = item['ItemID']
    color_id = item['ColorID']
    matching = available_parts.get((item_id, color_id), [])
    matching = list(sorted(matching, key=lambda x: -1 * x['cost_per_unit']))

    # take as much inventory as possible, starting with the lowest price, until
    # the requested quantity is filled
    n_remaining = item['Qty']
    while n_remaining > 0:
      if len(matching) == 0:
        print 'WARNING: couldn\'t find enough inventory to purchase %s' % (item['ItemName'],)
        cost = float('inf')
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
      cost += amount * next['cost_per_unit']

  return (cost, result)


def covers(wanted_parts, available_parts):
  """True if the given stores can cover all desired items"""
  kf = lambda x: (x['item_id'], x['wanted_color_id'])
  available_parts = utils.groupby(available_parts, kf)

  for item in wanted_parts:
    item_id = item['ItemID']
    color_id = item['ColorID']
    quantity = item['Qty']
    available = available_parts.get((item_id, color_id), [])
    inventory = sum(e['quantity_available'] for e in available)

    if inventory < quantity:
      return False
  return True


# TODO this doesn't work at all
def greedy(wanted_parts, price_guide):
  """Greedy Set-Cover algorithm to minimize number of stores purchased from.
  Disregards prices in decisions."""
  result = []

  available_parts = utils.groupby(price_guide, lambda x: x['store_id'])
  available_parts = copy.deepcopy(available_parts)

  wanted_parts = copy.deepcopy(wanted_parts)
  wanted_by_item = utils.groupby(wanted_parts, lambda x: (x['ItemID'], x['ColorID']))

  # while we don't have all the parts we need
  while len(wanted_parts) > 0 and len(available_parts) > 0:
    # calculate how many parts each vendor can cover
    def coverage(inventory):
      kf = lambda x: (x['item_id'], x['wanted_color_id'])
      # only worry about items wanted
      wanted = filter(lambda x: kf(x) in wanted_by_item, inventory)

      # count up how much there is of each (item_id, color_id) pair
      wanted = utils.groupby(wanted, kf)
      wanted = map(lambda x: (x[0], sum(e['quantity_available'] for e in x[1])),
                   wanted.iteritems())

      # count how much of each item I'd buy
      tot = 0
      for (k, v) in wanted:
        if k in wanted_by_item:
          tot += min(wanted_by_item[k][0]['Qty'], v)

      return tot

    coverages = [(k, v, coverage(v)) for (k, v) in available_parts.iteritems()]
    coverages = list(sorted(coverages, key=lambda x: x[2]))

    # use the store that has the most inventory
    next_store, inventory, n_parts = coverages.pop()
    print 'You can buy %d items from %s' % (n_parts, next_store)
    if n_parts == 0:
      break

    # update the quantities in the wanted parts list
    by_item = utils.groupby(inventory,
                            lambda x: (x['item_id'], x['wanted_color_id']))
    new_wanted_parts = []
    for item in wanted_parts:
      # get all lots from next_store matching item
      item_id = item['ItemID']
      color_id = item['ColorID']
      wanted_qty = item['Qty']

      available = by_item.get((item_id, color_id), [])
      available = list(sorted(available, key=lambda x: -1 * x['cost_per_unit']))

      # keep buying up lots until the wanted_qty is full or the store is bought
      # out
      while wanted_qty > 0 and len(available) > 0:
        next = available.pop()
        amount_to_buy = min(next['quantity_available'], wanted_qty)

        result.append({
          'store_id': next['store_id'],
          'quantity': amount_to_buy,
          'item_id': item_id,
          'color_id': next['color_id'],
          'wanted_color_id': next['wanted_color_id'],
          'cost_per_unit': next['cost_per_unit']
        })

        wanted_qty -= amount_to_buy

      # this store couldn't fill out our order
      if wanted_qty > 0:
        item['Qty'] = wanted_qty
        new_wanted_parts.append(item)

    # update wanted parts list, remove store from inventory
    wanted_parts = new_wanted_parts
    wanted_by_item = utils.groupby(wanted_parts,
                                   lambda x: (x['ItemID'], x['ColorID']))
    del available_parts[next_store]

    print 'Wanted parts left: %d' % sum(e['Qty'] for e in wanted_parts)


  if len(wanted_parts) > 0:
    print 'WARNING: there wasn\'t enough availability to buy the following items:'
    print ", ".join(e['ItemName'] for e in wanted_parts)

  cost = sum(e['quantity'] * e['cost_per_unit'] for e in result)
  store_ids = list(set(e['store_id'] for e in result))
  return [{
    'cost': cost,
    'allocation': result,
    'store_ids': store_ids
  }]
