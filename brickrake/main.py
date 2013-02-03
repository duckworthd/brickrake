import argparse
import traceback

from brickrake import color
from brickrake import io
from brickrake import minimizer
from brickrake import scraper

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--parts-list', required=True,
    help='BSX file containing desired parts')
parser.add_argument('--store-list', default=None,
    help='JSON file containing store metadata')
parser.add_argument('--country', default=None,
    help='limit search to stores in a particular country')
parser.add_argument('--feedback', default=100, type=int,
    help='limit search to stores with enough feedback')
parser.add_argument('--price-guide', default=None,
    help='Location to save price guide for wanted list')
parser.add_argument('--max-n-stores', default=5, type=int,
    help='Maximum number of different stores in a proposed solution')
parser.add_argument('--output', default='solutions.json',
    help='Where to save purchase recommendations')
args = parser.parse_args()

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
    print 'Catastrophic Failure!'
    traceback.print_exc()

# save price data
if args.price_guide is not None:
  io.save_price_guide(open(args.price_guide, 'w'), available_parts)

# decide on which stores to use
all_solutions = {}
for k in range(1, args.max_n_stores):
  solutions = minimizer.brute_force(wanted_parts, available_parts, k)
  solutions = list(sorted(solutions, key=lambda x: x['cost']))
  all_solutions[k] = solutions[0:10]

  print '%8s %40s' % ('Cost', 'Store IDs')
  for s in solutions[:10]:
    print '$%7.2f %40s' % (s['cost'], s['store_ids'])

# store solution
io.save_solutions(open(args.output, 'w'), all_solutions)
