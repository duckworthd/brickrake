#!/usr/bin/env python

import argparse
import os
import traceback

from brickrake import color
from brickrake import io
from brickrake import minimizer
from brickrake import scraper


def price_guide(args):
  """Scrape pricing information for all wanted parts"""
  # load in wanted parts
  wanted_parts = io.load_bsx(open(args.parts_list))
  print 'Loaded %d different parts' % len(wanted_parts)

  if args.store_list is not None:
    # load in store metadata
    store_metadata = io.load_store_metadata(open(args.store_list))
    print 'Loaded metadata for %d stores' % len(store_metadata)

    allowed_stores = [store for store in store_metadata]

    # select which stores to get parts from
    if args.country is not None:
      print 'Only allowing stores from %s' % (args.country,)
      allowed_stores = filter(lambda x: x['country_id'] == args.country, allowed_stores)

    if args.feedback is not None:
      print 'Only allowing stores with %d feedback' % (args.feedback,)
      allowed_stores = filter(lambda x: x['feedback'] >= args.feedback, allowed_stores)

    allowed_stores = map(lambda x: x['store_id'], allowed_stores)
    print 'Using %d stores' % len(allowed_stores)

  else:
    allowed_stores = None
    print 'Using all stores'

  # get prices for available parts
  available_parts = []
  for (i, item) in enumerate(wanted_parts):
    print '#%d: Retrieving availability for %d %s %s' % (i, item['Qty'], item['ColorName'], item['ItemName'])
    try:
      # fetch price data for this item in the closest available color
      new = scraper.price_guide(item, allowed_stores=allowed_stores)
      available_parts.extend(new)

      # print out status message
      total_quantity = sum(e['quantity_available'] for e in new)
      colors = [color.name(id) for id in set(e['color_id'] for e in new)]
      print 'Found %d available %s in the following colors: %s' % (total_quantity, item['ItemName'], colors)

      if total_quantity < item['Qty']:
        print 'WARNING! Couldn\'t find enough parts!'

    except Exception as e:
      print 'Catastrophic Failure! :('
      traceback.print_exc()

  # save price data
  io.save_price_guide(open(args.output, 'w'), available_parts)


def minimize(args):
  """Minimize the cost of a purchase"""
  # load in parts lists, pricing data
  wanted_parts = io.load_bsx(open(args.parts_list))
  available_parts = io.load_price_guide(open(args.price_guide))
  print 'Loaded %d different parts' % len(wanted_parts)

  # decide on which stores to use
  for k in range(1, args.max_n_stores):
    solutions = minimizer.brute_force(wanted_parts, available_parts, k)
    solutions = list(sorted(solutions, key=lambda x: x['cost']))
    solutions = solutions[0:10]

    if len(solutions) > 0:
      print '%8s %40s' % ('Cost', 'Store IDs')
      for s in solutions[:10]:
        print '$%7.2f %40s' % (s['cost'], s['store_ids'])
    else:
      print "No solutions using %d stores" % k

    # save output
    output_folder = os.path.join(args.output, str(k))
    try:
      os.makedirs(output_folder)
    except OSError:
      pass

    for (i, solution) in enumerate(solutions):
      output_path = os.path.join(output_folder, "%02d.json" % i)
      with open(output_path, 'w') as f:
        io.save_solution(f, solution)


def wanted_list(args):
  """Create BrickLink Wanted Lists for a purchase"""
  # load recommendation
  recommendation = io.load_solution(open(args.recommendation))
  io.save_bsx_per_vendor(args.output, recommendation)
  return


if __name__ == '__main__':
  parser = argparse.ArgumentParser("Brickrake: the BrickLink Store Recommendation Engine")
  subparsers = parser.add_subparsers()

  parser_pg = subparsers.add_parser("price_guide",
      help="Download pricing information from BrickLink")
  parser_pg.add_argument('--parts-list', required=True,
      help='BSX file containing desired parts')
  parser_pg.add_argument('--store-list', default=None,
      help='JSON file containing store metadata')
  parser_pg.add_argument('--country', default=None,
      help='limit search to stores in a particular country')
  parser_pg.add_argument('--feedback', default=100, type=int,
      help='limit search to stores with enough feedback')
  parser_pg.add_argument('--output', required=True,
      help='Location to save price guide for wanted list')
  parser_pg.set_defaults(func=price_guide)

  parser_mn = subparsers.add_parser("minimize",
      help="Find a small set of vendors to buy parts from")
  parser_mn.add_argument('--parts-list', required=True,
      help='BSX file containing desired parts')
  parser_mn.add_argument('--price-guide', required=True,
      help='Pricing information output by "brickrake price_guide"')
  parser_mn.add_argument('--max-n-stores', default=5, type=int,
      help='Maximum number of different stores in a proposed solution')
  parser_mn.add_argument('--output', required=True,
      help='Directory to save purchase recommendations')
  parser_mn.set_defaults(func=minimize)

  parser_wl = subparsers.add_parser("wanted_list",
      help="Create BrickLink Wanted Lists for each vendor")
  parser_wl.add_argument("--recommendation", required=True,
      help='JSON file output by "brickrake minimize"')
  parser_wl.add_argument("--output", required=True,
      help="Folder to create BrickLink Wanted List XML in")
  parser_wl.set_defaults(func=wanted_list)

  args = parser.parse_args()
  args.func(args)
