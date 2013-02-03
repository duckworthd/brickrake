"""
Tests for brickrake.minimizer
"""
from unittest import TestCase

from brickrake.minimizer import *


WANTED_PARTS = [
  {
    'ItemID': '123',
    'ColorID': 1,
    'Qty': 100,
    'ItemName': 'Item1',
  },
  {
    'ItemID': '123',
    'ColorID': 2,
    'Qty': 50,
    'ItemName': 'Item2',
  },
  {
    'ItemID': '456',
    'ColorID': 80,
    'Qty': 10,
    'ItemName': 'Item3',
  },
]

MISSING_PART = [
  {
    'item_id': '123',
    'wanted_color_id': 1,
    'color_id': 1,
    'cost_per_unit': 0.05,
    'store_id': 'one',
    'quantity_available': 120
  }
]

NOT_ENOUGH_INVENTORY = [
  {
    'item_id': '123',
    'wanted_color_id': 1,
    'color_id': 1,
    'cost_per_unit': 0.05,
    'store_id': 'one',
    'quantity_available': 120
  },
  {
    'item_id': '123',
    'wanted_color_id': 2,
    'color_id': 2,
    'cost_per_unit': 0.05,
    'store_id': 'one',
    'quantity_available': 52
  },
  {
    'item_id': '456',
    'wanted_color_id': 80,
    'color_id': 80,
    'cost_per_unit': 0.05,
    'store_id': 'one',
    'quantity_available': 5
  },
  {
    'item_id': '456',
    'wanted_color_id': 81,
    'color_id': 81,
    'cost_per_unit': 0.05,
    'store_id': 'one',
    'quantity_available': 20
  },
]

JUST_RIGHT = [
  {
    'item_id': '123',
    'wanted_color_id': 1,
    'color_id': 1,
    'cost_per_unit': 0.05,
    'store_id': 'one',
    'quantity_available': 120
  },
  {
    'item_id': '123',
    'wanted_color_id': 2,
    'color_id': 3,
    'cost_per_unit': 0.10,
    'store_id': 'one',
    'quantity_available': 30
  },
  {
    'item_id': '123',
    'wanted_color_id': 2,
    'color_id': 3,
    'cost_per_unit': 0.25,
    'store_id': 'two',
    'quantity_available': 25
  },
  {
    'item_id': '456',
    'wanted_color_id': 80,
    'color_id': 80,
    'cost_per_unit': 0.20,
    'store_id': 'one',
    'quantity_available': 10
  }
]

ALLOCATION = [
  {
    'item_id': '123',
    'color_id': 1,
    'store_id': 'one',
    'quantity': 100,
    'cost_per_unit': 0.05,
  },
  {
    'item_id': '123',
    'color_id': 3,
    'store_id': 'one',
    'quantity': 30,
    'cost_per_unit': 0.10,
  },
  {
    'item_id': '123',
    'color_id': 3,
    'store_id': 'two',
    'quantity': 20,
    'cost_per_unit': 0.25,
  },
  {
    'item_id': '456',
    'color_id': 80,
    'store_id': 'one',
    'quantity': 10,
    'cost_per_unit': 0.20,
  }
]


def test_covers():
  assert not covers(WANTED_PARTS, MISSING_PART)
  assert not covers(WANTED_PARTS, NOT_ENOUGH_INVENTORY)
  assert covers(WANTED_PARTS, JUST_RIGHT)


def test_min_cost():
  assert min_cost(WANTED_PARTS, NOT_ENOUGH_INVENTORY)[0] == float('inf')
  assert min_cost(WANTED_PARTS, MISSING_PART)[0] == float('inf')
  assert min_cost(WANTED_PARTS, JUST_RIGHT)[0] == sum(x['cost_per_unit'] * x['quantity'] for x in ALLOCATION)
  assert min_cost(WANTED_PARTS, JUST_RIGHT)[1] == ALLOCATION


def test_brute_force():
  assert brute_force(WANTED_PARTS, JUST_RIGHT, 1) == []
  assert brute_force(WANTED_PARTS, JUST_RIGHT, 2) == [{
    'cost': sum(x['cost_per_unit'] * x['quantity'] for x in ALLOCATION),
    'allocation': ALLOCATION,
    'store_ids': ('two', 'one')
  }]
