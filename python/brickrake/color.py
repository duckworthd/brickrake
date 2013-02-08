"""
Functions for finding similar colors
"""
import json
import math
import os

from colormath.color_objects import LabColor
from colormath.color_diff import delta_e_cie2000

# mapping from ColorID to Lab color space. Made using colors extracted from
# http://www.bricklink.com/catalogColors.asp and code from
# http://www.cse.unr.edu/~quiroz/inc/colortransforms.py
COLORS = dict(
    (int(k), v) for (k, v)
    in json.load(open(os.path.split(__file__)[0] + '/data/colors.json')).iteritems()
)


def similar_to(color_id):
  """Get a list of similar colors, by color id"""
  if color_id == 0:
    color_id = 9  # light grey

  color = COLORS[color_id]
  distances = sorted(
      (distance(color2['lab'], color['lab']), id)
      for (id, color2) in COLORS.items()
  )
  return [e[1] for e in distances]


def distance(color1, color2):
  """Color distance as defined by CIE76 (L2 norm)"""
  return delta_e_cie2000(LabColor(*color1), LabColor(*color2))


def name(color_id):
  """Get name of a color"""
  try:
    return COLORS[color_id]['name']
  except KeyError:
    return str(color_id)
