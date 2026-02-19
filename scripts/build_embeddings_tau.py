"""
scripts/build_embeddings_tau.py
================================
Compute cocktail embeddings using softmax-based perceptual strategy with tau parameter.
Generates stabilized UMAP embeddings across a range of tau values.

Run with:
    .venv/bin/python scripts/build_embeddings_tau.py
"""

import json
import sys
from pathlib import Path

import numpy as np

# Add project root to path so we can import loaders/utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from loaders import FLAVOR_DIMS, INGREDIENTS, RECIPES

try:
    import umap
except ImportError:
    print("ERROR: umap-learn not installed. Run: .venv/bin/pip install umap-learn")
    sys.exit(1)

DATA = Path(__file__).parent.parent / "data"
OUTPUT = DATA / "embeddings.json"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

FLAVOR_DIM_INDEX = {d: i for i, d in enumerate(FLAVOR_DIMS)}

_ROLE_GROUPS = {
    "modifier":  "modifying",
    "sweetener": "modifying",
    "accent":    "accent",
    "base":      "base",
    "citrus":    "citrus",
    "seasoning": "seasoning",
}

def get_flavor_vector(ingredient_name: str) -> np.ndarray:
    if ingredient_name not in INGREDIENTS:
        return np.zeros(len(FLAVOR_DIMS))
    ing = INGREDIENTS[ingredient_name]
    return np.array([ing["flavor"][dim] for dim in FLAVOR_DIMS])


def recipe_total_ml(recipe: dict) -> float:
    return sum(c["ml"] for c in recipe["components"] if c["ml"] is not None)


# ─────────────────────────────────────────────────────────────────────────────
# Original BLEND strategy (for comparison)
# ─────────────────────────────────────────────────────────────────────────────

def blend_vector(recipe: dict) -> np.ndarray:
    total_ml = recipe_total_ml(recipe)
    blended = np.zeros(len(FLAVOR_DIMS))
    for c in recipe["components"]:
        fv = get_flavor_vector(c["ingredient"])
        if c["ml"] is not None and total_ml > 0:
            weight = c["ml"] / total_ml
        else:
            weight = 0.05  # seasoning
        blended += fv * weight
    for g in recipe.get("garnish", []):
        blended += get_flavor_vector(g) * 0.03
    return blended


# ─────────────────────────────────────────────────────────────────────────────
# Softmax-based perceptual strategy with tau parameter
# ─────────────────────────────────────────────────────────────────────────────

def softmax(x: np.ndarray) -> np.ndarray:
    """Compute softmax values for array x."""
    exp_x = np.exp(x - np.max(x))  # subtract max for numerical stability
    return exp_x / exp_x.sum()


def softmax_perceptual_vector(recipe: dict, tau: float = 1.0) -> np.ndarray:
    """
    Compute perceptual vector using softmax over ingredient intensities,
    modulated by volume proportions.

    tau controls the sharpness of the intensity boost:
    - tau → 0: most intense ingredient dominates regardless of volume
    - tau = 1: balanced — intensity and volume both matter
    - tau → ∞: softmax flattens to uniform, so volume proportions win
               (converges to Flavor Blend)

    The key insight: softmax(intensity / tau) produces an intensity boost
    factor per ingredient. Multiplying by volume proportions and renormalizing
    means that at high tau the boost becomes uniform and volume alone
    determines the weights — exactly matching Flavor Blend.
    """
    total_ml = recipe_total_ml(recipe)
    ingredient_data = []

    # Collect ingredient vectors and volumes
    for c in recipe["components"]:
        fv = get_flavor_vector(c["ingredient"])
        if c["ml"] is not None and total_ml > 0:
            ml_weight = c["ml"] / total_ml
        else:
            ml_weight = 0.05  # seasoning
        ingredient_data.append((fv, ml_weight))

    # Add garnishes with small weight
    for g in recipe.get("garnish", []):
        fv = get_flavor_vector(g)
        ingredient_data.append((fv, 0.03))

    if not ingredient_data:
        return np.zeros(len(FLAVOR_DIMS))

    # Compute intensities (L2 norm of flavor vectors)
    flavor_vecs = np.array([d[0] for d in ingredient_data])
    ml_weights = np.array([d[1] for d in ingredient_data])
    intensities = np.linalg.norm(flavor_vecs, axis=1)

    # Step 1: softmax over intensities alone (the "boost" factor)
    # At low tau this concentrates on the most intense ingredient;
    # at high tau this flattens to uniform (1/n).
    if tau > 0:
        intensity_boost = softmax(intensities / tau)
    else:
        intensity_boost = np.zeros_like(intensities)
        intensity_boost[np.argmax(intensities)] = 1.0

    # Step 2: modulate by volume proportions and renormalize
    # At high tau: boost ≈ 1/n, so weights ∝ ml_weights → Flavor Blend
    # At low tau: boost concentrates on intense ingredients,
    #   volume still modulates but intense ingredients dominate
    weights = intensity_boost * ml_weights
    weight_sum = weights.sum()
    if weight_sum > 0:
        weights /= weight_sum

    # Compute weighted average of flavor vectors
    result = np.zeros(len(FLAVOR_DIMS))
    for i, (fv, _) in enumerate(ingredient_data):
        result += weights[i] * fv

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Derived fields
# ─────────────────────────────────────────────────────────────────────────────

def _top_level_category(ingredient_name: str) -> str | None:
    """Return the top-level category path of an ingredient."""
    if ingredient_name not in INGREDIENTS:
        return None
    path = INGREDIENTS[ingredient_name]["category_path"]
    return path[0] if path else None


def _second_level_category(ingredient_name: str) -> str | None:
    """Return the second-level category (e.g. 'whiskey', 'gin')."""
    if ingredient_name not in INGREDIENTS:
        return None
    path = INGREDIENTS[ingredient_name]["category_path"]
    return path[1] if len(path) > 1 else path[0] if path else None


def cocktail_base_spirit(recipe: dict) -> str | None:
    """
    Return the base spirit of the cocktail (whiskey, gin, rum, etc).
    If it has multiple base spirits, return the one with the most volume.
    """
    base_spirits = {}
    for c in recipe["components"]:
        if _top_level_category(c["ingredient"]) == "spirits" and c["ml"]:
            spirit = _second_level_category(c["ingredient"])
            if spirit:
                base_spirits[spirit] = base_spirits.get(spirit, 0) + c["ml"]
    if not base_spirits:
        return None
    return max(base_spirits, key=base_spirits.get)


def cocktail_family(recipe: dict) -> str | None:
    """
    Return a high-level family classification of the cocktail.
    This is a heuristic based on the recipe structure and ingredients.
    """
    has_citrus = any(c["role"] == "citrus" for c in recipe["components"])
    has_sweetener = any(c["role"] == "sweetener" for c in recipe["components"])
    has_modifier = any(c["role"] in ["modifier", "accent"] for c in recipe["components"])
    has_soda = any("soda" in c["ingredient"].lower() or "tonic" in c["ingredient"].lower()
                   for c in recipe["components"])
    has_egg = any("egg" in c["ingredient"].lower() or "aquafaba" in c["ingredient"].lower()
                  for c in recipe["components"])

    # served style
    served = recipe.get("served", "").lower()
    up = served == "up"
    on_ice = served == "on_ice"

    # Classification heuristics (order matters)
    if has_citrus and has_sweetener:
        if has_egg:
            return "sour_foam"
        elif has_soda:
            return "collins"
        else:
            return "sour"
    elif has_modifier and not has_citrus:
        if up:
            return "martini"
        else:
            return "old_fashioned"
    elif has_soda:
        return "highball"
    else:
        return "other"


# ─────────────────────────────────────────────────────────────────────────────
# Main: Generate embeddings across tau range with stabilization
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Load recipes and sort by name
    recipe_names = sorted(RECIPES.keys())
    recipes = {name: RECIPES[name] for name in recipe_names}

    print(f"Loaded {len(recipes)} recipes")

    # Define tau range - we'll use log spacing for better coverage
    # tau_values = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
    # Actually, let's make it finer for smooth animation
    tau_values = np.logspace(-1, 2.5, 25)  # from 0.1 to ~316, 25 steps
    tau_values = np.round(tau_values, 3).tolist()

    print(f"Tau values: {tau_values}")

    # Choose central tau for initial embedding
    central_tau_idx = len(tau_values) // 2
    central_tau = tau_values[central_tau_idx]

    print(f"Starting with central tau = {central_tau}")

    # Compute vectors for central tau
    print(f"Computing vectors for tau = {central_tau}...")
    vectors_central = np.array([
        softmax_perceptual_vector(recipes[n], tau=central_tau)
        for n in recipe_names
    ])

    # Compute initial UMAP embedding at central tau
    print(f"Computing initial UMAP embedding at tau = {central_tau}...")
    reducer = umap.UMAP(
        n_neighbors=10,
        n_components=2,
        metric="cosine",
        min_dist=0.1,
        random_state=42,
    )
    embedding_central = reducer.fit_transform(vectors_central)

    # Store embeddings
    embeddings_by_tau = {
        central_tau: embedding_central.tolist()
    }

    # Work outward from center in both directions
    # First, go downward (decreasing tau)
    prev_embedding = embedding_central
    for i in range(central_tau_idx - 1, -1, -1):
        tau = tau_values[i]
        print(f"Computing embedding for tau = {tau} (using previous as init)...")

        # Compute vectors for this tau
        vectors = np.array([
            softmax_perceptual_vector(recipes[n], tau=tau)
            for n in recipe_names
        ])

        # Use previous embedding as initialization
        reducer = umap.UMAP(
            n_neighbors=10,
            n_components=2,
            metric="cosine",
            min_dist=0.1,
            random_state=42,
            init=prev_embedding,  # Key: use previous positions
        )
        embedding = reducer.fit_transform(vectors)
        embeddings_by_tau[tau] = embedding.tolist()
        prev_embedding = embedding

    # Then go upward (increasing tau)
    prev_embedding = embedding_central
    for i in range(central_tau_idx + 1, len(tau_values)):
        tau = tau_values[i]
        print(f"Computing embedding for tau = {tau} (using previous as init)...")

        # Compute vectors for this tau
        vectors = np.array([
            softmax_perceptual_vector(recipes[n], tau=tau)
            for n in recipe_names
        ])

        # Use previous embedding as initialization
        reducer = umap.UMAP(
            n_neighbors=10,
            n_components=2,
            metric="cosine",
            min_dist=0.1,
            random_state=42,
            init=prev_embedding,  # Key: use previous positions
        )
        embedding = reducer.fit_transform(vectors)
        embeddings_by_tau[tau] = embedding.tolist()
        prev_embedding = embedding

    # Also compute original BLEND strategy for comparison
    print("Computing BLEND embeddings for comparison...")
    blend_vecs = np.array([blend_vector(recipes[n]) for n in recipe_names])
    reducer_blend = umap.UMAP(
        n_neighbors=10,
        n_components=2,
        metric="cosine",
        min_dist=0.1,
        random_state=42,
    )
    blend_embedding = reducer_blend.fit_transform(blend_vecs)

    # Build output structure
    print("Building output JSON...")

    # First, build the recipe data with derived fields
    recipe_data = {}
    for name in recipe_names:
        recipe = recipes[name]
        recipe_data[name] = {
            "base_spirit": cocktail_base_spirit(recipe),
            "family": cocktail_family(recipe),
            "served": recipe.get("served"),
            "flavor_profile": {
                dim: sum(
                    INGREDIENTS[c["ingredient"]]["flavor"][dim] *
                    (c["ml"] / recipe_total_ml(recipe) if c["ml"] else 0.05)
                    for c in recipe["components"]
                    if c["ingredient"] in INGREDIENTS
                ) for dim in FLAVOR_DIMS
            }
        }

    # Read existing embeddings to preserve other strategies
    existing_data = {}
    if OUTPUT.exists():
        with open(OUTPUT, "r") as f:
            existing_data = json.load(f)

    # Build the tau-parameterized embeddings
    tau_embeddings = {}
    for tau in sorted(embeddings_by_tau.keys()):
        embedding = embeddings_by_tau[tau]
        tau_embeddings[str(tau)] = {
            "description": f"Softmax perceptual with τ={tau}",
            "embedding": {
                name: {"x": float(embedding[i][0]), "y": float(embedding[i][1])}
                for i, name in enumerate(recipe_names)
            }
        }

    # Preserve existing strategies and add tau variations
    output = {
        "recipes": existing_data.get("recipes", recipe_data),
        "strategies": existing_data.get("strategies", {}),
    }

    # Add tau embeddings as a new strategy type
    output["strategies"]["tau"] = tau_embeddings

    # Write output
    print(f"Writing to {OUTPUT}...")
    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Successfully wrote embeddings for {len(recipes)} recipes")
    print(f"Generated {len(tau_values)} tau variations with spatial continuity")


if __name__ == "__main__":
    main()