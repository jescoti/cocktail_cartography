"""
utils.py
========
Distance and vector utilities for cocktail clustering.
All data is read from loaders.py (which reads data/).
"""

import numpy as np

from loaders import FLAVOR_DIMS, INGREDIENTS, RECIPES


# ---------------------------------------------------------------------------
# Ingredient utilities
# ---------------------------------------------------------------------------

def get_flavor_vector(ingredient_name: str) -> np.ndarray:
    """Ordered flavor vector for a single ingredient."""
    ing = INGREDIENTS[ingredient_name]
    return np.array([ing["flavor"][dim] for dim in FLAVOR_DIMS])


def ingredient_flavor_distance(a: str, b: str) -> float:
    """Cosine distance between two ingredient flavor profiles (0 = identical)."""
    va, vb = get_flavor_vector(a), get_flavor_vector(b)
    norm_a, norm_b = np.linalg.norm(va), np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - np.dot(va, vb) / (norm_a * norm_b)


def category_distance(a: str, b: str) -> int:
    """
    Tree distance between two ingredients based on category taxonomy.
    Returns (depth_a - common) + (depth_b - common), i.e. hops to LCA * 2.
    """
    cat_a = INGREDIENTS[a]["category_path"]
    cat_b = INGREDIENTS[b]["category_path"]
    common = sum(1 for x, y in zip(cat_a, cat_b) if x == y)
    return (len(cat_a) - common) + (len(cat_b) - common)


# ---------------------------------------------------------------------------
# Recipe utilities
# ---------------------------------------------------------------------------

def compute_recipe_proportions(recipe_name: str) -> dict:
    """Return recipe dict with 'proportion' added to each component."""
    recipe = RECIPES[recipe_name]
    total_ml = sum(c["ml"] for c in recipe["components"] if c["ml"] is not None)
    components = []
    for c in recipe["components"]:
        prop = (c["ml"] / total_ml) if c["ml"] is not None else None
        components.append({**c, "proportion": round(prop, 3) if prop is not None else None})
    return {**recipe, "components": components, "total_ml": total_ml}


def recipe_flavor_vector(recipe_name: str) -> np.ndarray:
    """
    Proportion-weighted blend of component flavor vectors.
    Seasonings: fixed weight 0.05. Garnishes: fixed weight 0.03.
    """
    recipe = RECIPES[recipe_name]
    total_ml = sum(c["ml"] for c in recipe["components"] if c["ml"] is not None)
    blended = np.zeros(len(FLAVOR_DIMS))

    for c in recipe["components"]:
        if c["ingredient"] not in INGREDIENTS:
            continue
        fv = get_flavor_vector(c["ingredient"])
        weight = (c["ml"] / total_ml) if (c["ml"] is not None and total_ml > 0) else 0.05
        blended += fv * weight

    for g in recipe.get("garnish", []):
        if g in INGREDIENTS:
            blended += get_flavor_vector(g) * 0.03

    return blended


def recipe_structural_vector(recipe_name: str) -> dict:
    """Structural features: method, served, role proportions, component counts."""
    recipe = RECIPES[recipe_name]
    total_ml = sum(c["ml"] for c in recipe["components"] if c["ml"] is not None)
    role_proportions = {}
    for c in recipe["components"]:
        if c["ml"] is not None and total_ml > 0:
            role = c["role"]
            role_proportions[role] = role_proportions.get(role, 0) + c["ml"] / total_ml
    return {
        "method": recipe["method"],
        "served": recipe["served"],
        "role_proportions": role_proportions,
        "n_components": len(recipe["components"]),
        "n_seasonings": sum(1 for c in recipe["components"] if c["ml"] is None),
        "has_garnish": len(recipe.get("garnish", [])) > 0,
    }


# Role grouping for structural comparison:
# "modifier" and "sweetener" are merged because sweet vermouth in a Manhattan
# plays the same structural role as sugar in an Old Fashioned.
_ROLE_GROUPS = {
    "modifier":  "modifying",
    "sweetener": "modifying",
    "accent":    "accent",
    "base":      "base",
    "citrus":    "citrus",
    "seasoning": "seasoning",
}


def recipe_distance(a: str, b: str, alpha: float = 0.5, beta: float = 0.5) -> float:
    """
    Combined distance between two recipes:
      alpha * flavor_distance + beta * structural_distance

    Flavor:     cosine distance of proportion-weighted flavor vectors.
    Structural: method penalty + serving penalty + euclidean role-proportion distance.
    """
    # --- Flavor ---
    fv_a, fv_b = recipe_flavor_vector(a), recipe_flavor_vector(b)
    norm_a, norm_b = np.linalg.norm(fv_a), np.linalg.norm(fv_b)
    flavor_dist = (
        1.0 if (norm_a == 0 or norm_b == 0)
        else 1.0 - np.dot(fv_a, fv_b) / (norm_a * norm_b)
    )

    # --- Structural ---
    sa, sb = recipe_structural_vector(a), recipe_structural_vector(b)

    method_dist = 0.0 if sa["method"] == sb["method"] else 0.15

    if sa["served"] == sb["served"]:
        served_dist = 0.0
    elif "either" in (sa["served"], sb["served"]):
        served_dist = 0.05
    else:
        served_dist = 0.15

    def group_props(role_props):
        grouped = {}
        for role, prop in role_props.items():
            g = _ROLE_GROUPS.get(role, role)
            grouped[g] = grouped.get(g, 0.0) + prop
        return grouped

    ga, gb = group_props(sa["role_proportions"]), group_props(sb["role_proportions"])
    all_groups = set(ga) | set(gb)
    role_dist = np.sqrt(sum((ga.get(g, 0.0) - gb.get(g, 0.0)) ** 2 for g in all_groups))

    structural_dist = min(method_dist + served_dist + role_dist, 1.0)

    return alpha * flavor_dist + beta * structural_dist
