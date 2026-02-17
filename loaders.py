"""
loaders.py
==========
Load cocktail data from the data/ directory into Python dicts.

  CATEGORY_TREE  — nested dict from taxonomy.json
  INGREDIENTS    — dict keyed by name, value has category_path, abv, flavor
  RECIPES        — dict keyed by name from recipes.json
  FLAVOR_DIMS    — ordered list of flavor dimension names (from CSV header)
"""

import csv
import json
from pathlib import Path

_DATA = Path(__file__).parent / "data"


def load_taxonomy() -> dict:
    with open(_DATA / "taxonomy.json") as f:
        return json.load(f)


def load_recipes() -> dict:
    with open(_DATA / "recipes.json") as f:
        return json.load(f)


def load_ingredients() -> tuple[list[str], dict]:
    """
    Returns (flavor_dims, ingredients) where:
      flavor_dims  — ordered list of dimension names, e.g. ["sweet", "bitter", ...]
      ingredients  — dict[name -> {category_path, abv, flavor: {dim -> float}}]
    """
    flavor_dims = None
    ingredients = {}

    with open(_DATA / "ingredients.csv", newline="") as f:
        reader = csv.DictReader(f)
        # Derive flavor dims from header: everything after name, category_path, abv
        fixed_cols = {"name", "category_path", "abv"}
        flavor_dims = [c for c in reader.fieldnames if c not in fixed_cols]

        for row in reader:
            name = row["name"]
            ingredients[name] = {
                "category_path": row["category_path"].split("|"),
                "abv": float(row["abv"]),
                "flavor": {dim: float(row[dim]) for dim in flavor_dims},
            }

    return flavor_dims, ingredients


# Module-level singletons — loaded once on first import
CATEGORY_TREE = load_taxonomy()
FLAVOR_DIMS, INGREDIENTS = load_ingredients()
RECIPES = load_recipes()
