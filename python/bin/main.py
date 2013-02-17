#!/usr/bin/env python

import argparse
import os
import traceback

from brickrake import color
from brickrake import io
from brickrake import minimizer
from brickrake import scraper
from brickrake import utils


def price_guide(args):
  """Scrape pricing information for all wanted parts"""
  # load in wanted parts
  if args.parts_list.endswith(".bsx"):
    wanted_parts = io.load_bsx(open(args.parts_list))
  else:
    wanted_parts = io.load_xml(open(args.parts_list))
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

    if args.include is not None:
      includes = args.include.strip().split(",")
      includes = map(lambda x: int(x), includes)
      print 'Forcing inclusion of: %s' % (includes,)
      for store in includes:
        allowed_stores.append({'store_id': store})

    if args.exclude is not None:
      excludes = set(args.exclude.strip().split(","))
      excludes = map(lambda x: int(x), excludes)
      print 'Forcing exclusion of: %s' % (excludes,)
      allowed_stores = filter(lambda x: not (x['store_id'] in excludes), allowed_stores)

    allowed_stores = map(lambda x: x['store_id'], allowed_stores)
    allowed_stores = list(set(allowed_stores))
    print 'Using %d stores' % len(allowed_stores)

  else:
    allowed_stores = None
    print 'Using all stores'

  # get prices for available parts
  fmt = "{i:4d} {status:10s} {name:60s} {color:30s} {quantity:5d}"
  print "{i:4s} {status:10s} {name:60s} {color:30s} {quantity:5s}" \
      .format(i="i", status="status", name="name", color="color", quantity="qty")
  print (4 + 1 + 10 + 1 + 60 + 1 + 30 + 1 + 5) * "-"

  if args.resume:
    old_parts = io.load_price_guide(open(args.resume))
    old_parts = utils.groupby(old_parts, lambda x: (x['item_id'], x['wanted_color_id']))
  else:
    old_parts = {}

  available_parts = []

  for (i, item) in enumerate(wanted_parts):
    # skip this item if we already have enough
    matching = old_parts.get( (item['ItemID'], item['ColorID']), [])
    quantity_found = sum(e['quantity_available'] for e in matching)

    print fmt.format(i=i, status="seeking", name=item['ItemName'], color=item['ColorName'], quantity=item['Qty'])

    if quantity_found >= item['Qty']:
      colors = [color.name(id) for id in set(e['color_id'] for e in matching)]
      print fmt.format(i=i, status="passing", name=item['ItemName'], color=",".join(colors), quantity=quantity_found)
      available_parts.extend(matching)
    else:
      try:
        # fetch price data for this item in the closest available color
        new = scraper.price_guide(item, allowed_stores=allowed_stores,
                                  max_cost_quantile=args.max_price_quantile)
        available_parts.extend(new)

        # print out status message
        total_quantity = sum(e['quantity_available'] for e in new)
        colors = [color.name(id) for id in set(e['color_id'] for e in new)]
        print fmt.format(i=i, status="found", name=item['ItemName'], color=",".join(colors), quantity=total_quantity)

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
  if args.parts_list.endswith(".bsx"):
    wanted_parts = io.load_bsx(open(args.parts_list))
  else:
    wanted_parts = io.load_xml(open(args.parts_list))
  print 'Loaded %d different parts' % len(wanted_parts)

  available_parts = io.load_price_guide(open(args.price_guide))
  n_available = len(available_parts)
  n_stores = len(set(e['store_id'] for e in available_parts))
  print 'Loaded %d available lots from %d stores' % (n_available, n_stores)

  if args.algorithm in ['ilp', 'greedy']:
    if args.algorithm == 'ilp':
      ### Integer Linear Programming ###
      solution = minimizer.gurobi(
          wanted_parts,
          available_parts,
          shipping_cost=args.shipping_cost
      )[0]
    elif args.algorithm == 'greedy':
      ### Greedy Set Cover ###
      solution = minimizer.greedy(wanted_parts, available_parts)[0]

    # check and save
    io.save_solution(open(args.output + ".json", 'w'), solution)

    # print outs
    stores = set(e['store_id'] for e in solution['allocation'])
    cost = solution['cost']
    unsatisified =  minimizer.unsatisified(wanted_parts, solution['allocation'])
    print 'Total cost: $%.2f | n_stores: %d | remaining: %d' % (cost, len(stores), len(unsatisified))


  elif args.algorithm == 'brute-force':
    # for each possible number of stores
    for k in range(1, args.max_n_stores):
      # find all possible solutions using k stores
      solutions = minimizer.brute_force(wanted_parts, available_parts, k)
      solutions = list(sorted(solutions, key=lambda x: x['cost']))
      solutions = solutions[0:10]

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

      # print outs
      if len(solutions) > 0:
        print '%8s %40s' % ('Cost', 'Store IDs')
        for sol in solutions:
          print '$%7.2f %40s' % (sol['cost'], ",".join(str(s) for s in sol['store_ids']))
      else:
        print "No solutions using %d stores" % k


def wanted_list(args):
  """Create BrickLink Wanted Lists for each store"""
  # load recommendation
  recommendation = io.load_solution(open(args.recommendation))
  io.save_xml_per_vendor(args.output, recommendation)


def store_list(args):
  """Get metadata for stores"""
  info = scraper.store_info(country=args.country)
  io.save_store_metadata(open(args.output, 'w'), info)


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
  parser_pg.add_argument('--feedback', default=0, type=int,
      help='limit search to stores with enough feedback')
  parser_pg.add_argument('--include', default=None,
      help='Force inclusion of the following comma-separated store IDs')
  parser_pg.add_argument('--exclude', default=None,
      help='Force exclusion of the following comma-separated store IDs')
  parser_pg.add_argument('--max-price-quantile', default=1.0, type=float,
      help=('Ignore lots that cost more than this quantile' +
            ' of the price distribution per item'))
  parser_pg.add_argument('--resume', default=None,
      help='Resume a previously run price_guide search')
  parser_pg.add_argument('--output', required=True,
      help='Location to save price guide for wanted list')
  parser_pg.set_defaults(func=price_guide)

  parser_mn = subparsers.add_parser("minimize",
      help="Find a small set of vendors to buy parts from")
  parser_mn.add_argument('--parts-list', required=True,
      help='BSX file containing desired parts')
  parser_mn.add_argument('--price-guide', required=True,
      help='Pricing information output by "brickrake price_guide"')
  parser_mn.add_argument('--algorithm', default='ilp',
      choices=['ilp', 'brute-force', 'greedy'],
      help='Algorithm used to select vendors')
  parser_mn.add_argument('--max-n-stores', default=5, type=int,
      help=('Maximum number of different stores in a proposed solution.' +
        'Only used if algorithm=brute-force.'))
  parser_mn.add_argument('--shipping-cost', default=10.0, type=float,
      help=('Estimated cost of shipping per store. ' + 
        'Only used if algorithm=ilp'))
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

  parser_st = subparsers.add_parser("stores",
      help="Download metadata about stores")
  parser_st.add_argument("--country", default=None,
      help="Only gather metadata for stores from this country")
  parser_st.add_argument("--output", required=True,
      help="Folder to create BrickLink Wanted List XML in")
  parser_st.set_defaults(func=store_list)

  args = parser.parse_args()
  args.func(args)
