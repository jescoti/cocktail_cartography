"""
Validation script — run with:  python -m cocktail_cortex
or directly:                   python __main__.py
"""

import numpy as np

from loaders import INGREDIENTS, RECIPES
from utils import (
    compute_recipe_proportions,
    ingredient_flavor_distance,
    category_distance,
    recipe_distance,
)

SEP = "=" * 60


def main():
    print(SEP)
    print("COCKTAIL CLUSTERING — VALIDATION")
    print(SEP)

    # --- Recipe proportions ---
    spotlight = ["martinez", "manhattan", "old_fashioned", "bijou", "last_word",
                 "margarita", "vieux_carre"]
    for name in spotlight:
        props = compute_recipe_proportions(name)
        print(f"\n{name.upper()} ({props['method']}, served {props['served']})")
        for c in props["components"]:
            if c["proportion"] is not None:
                print(f"  {c['ingredient']:22s}  {c['role']:12s}  {c['ml']:5.1f}ml  ({c['proportion']:.1%})")
            else:
                print(f"  {c['ingredient']:22s}  {c['role']:12s}  seasoning")
        if props.get("garnish"):
            print(f"  garnish: {', '.join(props['garnish'])}")

    # --- Recipe distance checks ---
    print(f"\n{SEP}\nKEY RECIPE DISTANCES\n{SEP}")
    pairs = [
        ("manhattan",    "old_fashioned",   "should be CLOSE"),
        ("bijou",        "tipperary",        "should be VERY CLOSE (spirit swap only)"),
        ("martinez",     "manhattan",        "should be MODERATE (same structure, different spirit)"),
        ("martinez",     "last_word",        "should be FAR (different families)"),
        ("last_word",    "final_ward",       "should be CLOSE (spirit+citrus swap)"),
        ("last_word",    "naked_and_famous", "should be CLOSE (all swaps, same structure)"),
        ("martini",      "martini_olive",    "should be VERY CLOSE (garnish only)"),
        ("margarita",    "daiquiri",         "should be CLOSE (same sour template)"),
    ]
    for a, b, note in pairs:
        d = recipe_distance(a, b)
        print(f"  {a:22s} <-> {b:22s}  {d:.4f}  ({note})")

    # --- Ingredient distances ---
    print(f"\n{SEP}\nINGREDIENT FLAVOR DISTANCES\n{SEP}")
    ing_pairs = [
        ("bourbon",       "rye_whiskey",    "should be VERY CLOSE"),
        ("bourbon",       "gin",            "should be FAR"),
        ("sweet_vermouth","averna",         "should be CLOSE (both sweet+bitter)"),
        ("sweet_vermouth","dry_vermouth",   "should be MODERATE"),
        ("green_chartreuse","benedictine",  "should be CLOSE-ish"),
        ("green_chartreuse","simple_syrup", "should be FAR"),
        ("lemon_juice",   "lime_juice",     "should be VERY CLOSE"),
    ]
    for a, b, note in ing_pairs:
        fd = ingredient_flavor_distance(a, b)
        cd = category_distance(a, b)
        print(f"  {a:22s} <-> {b:22s}  flavor={fd:.4f}  cat={cd}  ({note})")

    # --- Full distance matrix ---
    print(f"\n{SEP}\nFULL RECIPE DISTANCE MATRIX\n{SEP}")
    recipe_names = list(RECIPES.keys())
    n = len(recipe_names)
    short = [r[:12] for r in recipe_names]
    header = f"{'':22s} " + " ".join(f"{s:>8s}" for s in short)
    print(header)
    print("-" * len(header))

    dist_matrix = np.zeros((n, n))
    for i, a in enumerate(recipe_names):
        row = f"{a:22s} "
        for j, b in enumerate(recipe_names):
            d = recipe_distance(a, b)
            dist_matrix[i, j] = d
            row += f"{d:8.3f} "
        print(row)

    # --- Nearest neighbors ---
    print(f"\n{SEP}\nNEAREST NEIGHBORS (top 5)\n{SEP}")
    for i, name in enumerate(recipe_names):
        neighbors = sorted(
            [(recipe_names[j], dist_matrix[i, j]) for j in range(n) if i != j],
            key=lambda x: x[1],
        )
        print(f"\n  {name}:")
        for nbr, d in neighbors[:5]:
            print(f"    {d:.4f}  {nbr}")


if __name__ == "__main__":
    main()
