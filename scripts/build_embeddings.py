"""
scripts/build_embeddings.py
============================
Compute cocktail embeddings under 4 vectorization strategies, run UMAP to 2D,
and write data/embeddings.json.

Run with:
    .venv/bin/python scripts/build_embeddings.py
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
    from umap import AlignedUMAP
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
# Strategy 1: BLEND — proportion-weighted flavor blend
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
# Strategy 2: BLEND+STRUCT — flavor blend concatenated with structural vector
# ─────────────────────────────────────────────────────────────────────────────

def structural_vector(recipe: dict) -> np.ndarray:
    total_ml = recipe_total_ml(recipe)
    role_ml = {"base": 0.0, "modifying": 0.0, "citrus": 0.0, "accent": 0.0}
    has_seasoning = 0

    for c in recipe["components"]:
        role = _ROLE_GROUPS.get(c["role"], c["role"])
        if c["ml"] is not None and total_ml > 0:
            if role in role_ml:
                role_ml[role] += c["ml"] / total_ml
        else:
            has_seasoning = 1

    is_up     = 1 if recipe.get("served") == "up"     else 0
    is_on_ice = 1 if recipe.get("served") == "on_ice" else 0

    return np.array([
        role_ml["base"],
        role_ml["modifying"],
        role_ml["citrus"],
        role_ml["accent"],
        has_seasoning,
        is_up,
        is_on_ice,
    ])


def blend_struct_vector_pair(recipe: dict) -> tuple[np.ndarray, np.ndarray]:
    """
    Return (flavor_unit, struct_unit): each half independently normalized to
    unit length. Normalizing before concatenating ensures alpha/beta controls
    a true soft interpolation between the two, not a magnitude-dominated one.
    """
    fv = blend_vector(recipe)
    sv = structural_vector(recipe)
    fn = np.linalg.norm(fv)
    sn = np.linalg.norm(sv)
    fv_unit = fv / fn if fn > 0 else fv
    sv_unit = sv / sn if sn > 0 else sv
    return fv_unit, sv_unit


def blend_struct_vector(recipe: dict, alpha: float = 0.5) -> np.ndarray:
    """
    Concatenate unit-normalized flavor (×alpha) and structural (×(1-alpha)).
    alpha=1 → pure flavor; alpha=0 → pure structure.
    Because both halves are unit-normalized first, the slider is a genuine
    interpolation rather than being dominated by whichever half has larger raw magnitude.
    """
    fv_unit, sv_unit = blend_struct_vector_pair(recipe)
    return np.concatenate([fv_unit * alpha, sv_unit * (1.0 - alpha)])


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 3: ROLE-SLOT — flavor profile of each structural slot
# ─────────────────────────────────────────────────────────────────────────────

SLOTS = ["base", "modifying", "citrus", "accent"]

def role_slot_vector(recipe: dict) -> np.ndarray:
    """4 × 15 = 60 dimensional vector: flavor profile per role slot."""
    total_ml = recipe_total_ml(recipe)
    slot_vecs  = {s: np.zeros(len(FLAVOR_DIMS)) for s in SLOTS}
    slot_total = {s: 0.0 for s in SLOTS}

    for c in recipe["components"]:
        role = _ROLE_GROUPS.get(c["role"], None)
        if role not in SLOTS:
            role = None  # seasoning — distribute later
        fv = get_flavor_vector(c["ingredient"])

        if c["ml"] is not None and total_ml > 0:
            if role:
                slot_vecs[role]  += fv * c["ml"]
                slot_total[role] += c["ml"]
        else:
            # Seasoning: add a small fixed contribution to all slots
            for s in SLOTS:
                slot_vecs[s] += fv * 0.05 / len(SLOTS)

    # Normalize each slot by its total volume (gives volume-weighted average)
    for s in SLOTS:
        if slot_total[s] > 0:
            slot_vecs[s] /= slot_total[s]
        # If slot is empty it stays as zeros

    # Garnish flavor → accent slot
    for g in recipe.get("garnish", []):
        slot_vecs["accent"] += get_flavor_vector(g) * 0.03

    return np.concatenate([slot_vecs[s] for s in SLOTS])


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 4: PERCEPTUAL — max ingredient punches above its weight
# ─────────────────────────────────────────────────────────────────────────────

PUNCH_WEIGHT = 0.4

def perceptual_vector(recipe: dict) -> np.ndarray:
    total_ml = recipe_total_ml(recipe)
    ingredient_vecs = []

    for c in recipe["components"]:
        fv = get_flavor_vector(c["ingredient"])
        ingredient_vecs.append(fv)

    for g in recipe.get("garnish", []):
        ingredient_vecs.append(get_flavor_vector(g) * 0.03)

    if not ingredient_vecs:
        return np.zeros(len(FLAVOR_DIMS))

    stacked = np.array(ingredient_vecs)
    max_vec  = stacked.max(axis=0)
    blend    = blend_vector(recipe)

    return PUNCH_WEIGHT * max_vec + (1 - PUNCH_WEIGHT) * blend


# ─────────────────────────────────────────────────────────────────────────────
# Derived fields: base_spirit and family
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


def derive_base_spirit(recipe: dict) -> str:
    """Find the dominant base ingredient and return its spirit subcategory."""
    bases = [c for c in recipe["components"] if c["role"] == "base" and c["ml"] is not None]
    if not bases:
        return "other"

    # Sort by volume descending
    bases = sorted(bases, key=lambda c: c["ml"], reverse=True)

    spirit_types = set()
    for b in bases:
        top = _top_level_category(b["ingredient"])
        if top == "spirit":
            sub = _second_level_category(b["ingredient"])
            if sub:
                spirit_types.add(sub)

    if not spirit_types:
        # Non-spirit base (e.g. vermouth-forward drinks)
        top = _top_level_category(bases[0]["ingredient"])
        return top or "other"

    if len(spirit_types) == 1:
        return list(spirit_types)[0]
    return "mixed"


def derive_family(recipe: dict) -> str:
    """Classify recipe into sour / spirit_forward / built / other."""
    roles = {c["role"] for c in recipe["components"]}
    has_citrus   = "citrus"   in roles
    has_modifier = "modifier" in roles or "sweetener" in roles

    if has_citrus:
        return "sour"
    if recipe.get("served") == "on_ice" and not has_modifier:
        return "built"
    if has_modifier:
        return "spirit_forward"
    return "other"


# ─────────────────────────────────────────────────────────────────────────────
# UMAP
# ─────────────────────────────────────────────────────────────────────────────

def run_umap(matrix: np.ndarray, n_neighbors: int = 10) -> np.ndarray:
    """Run UMAP on rows of matrix, return Nx2 array."""
    reducer = umap.UMAP(
        n_components=2,
        metric="cosine",
        n_neighbors=min(n_neighbors, len(matrix) - 1),
        min_dist=0.1,
        random_state=42,
    )
    return reducer.fit_transform(matrix)


def procrustes_align(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """
    Align `source` to `target` using rotation + reflection only (no scaling).
    Both arrays are Nx2. Returns the rotated/reflected `source`.

    Algorithm: SVD-based orthogonal Procrustes (Schönemann 1966).
    We center both, find the best rotation R = V @ U.T, then re-center
    the result at the target centroid.
    """
    # Center both
    mu_src = source.mean(axis=0)
    mu_tgt = target.mean(axis=0)
    S = source - mu_src
    T = target - mu_tgt

    # SVD of cross-covariance
    M = T.T @ S
    U, _, Vt = np.linalg.svd(M)
    # Ensure a proper rotation (det = +1, not a reflection)
    d = np.linalg.det(U @ Vt)
    D = np.diag([1, np.sign(d)])
    R = U @ D @ Vt

    aligned = (S @ R.T) + mu_tgt
    return aligned


# ─────────────────────────────────────────────────────────────────────────────
# Nearest neighbours (cosine distance) from raw high-dim vectors
# ─────────────────────────────────────────────────────────────────────────────

def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 1.0
    return float(1.0 - np.dot(a, b) / (na * nb))


def nearest_neighbors(names: list[str], vectors: np.ndarray, top_k: int = 5) -> dict:
    """Return {name: [{name, distance}, ...]} for each cocktail."""
    result = {}
    n = len(names)
    for i, name in enumerate(names):
        dists = []
        for j, other in enumerate(names):
            if i != j:
                d = cosine_distance(vectors[i], vectors[j])
                dists.append({"name": other, "distance": round(d, 4)})
        dists.sort(key=lambda x: x["distance"])
        result[name] = dists[:top_k]
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    recipe_names = list(RECIPES.keys())
    recipes      = {n: RECIPES[n] for n in recipe_names}
    n = len(recipe_names)

    print(f"Building embeddings for {n} recipes …")

    # ── Per-recipe derived metadata ──────────────────────────────────────────
    recipe_meta = {}
    for name, recipe in recipes.items():
        flavor_vec = blend_vector(recipe)
        recipe_meta[name] = {
            "method":       recipe["method"],
            "served":       recipe.get("served", "either"),
            "components":   recipe["components"],
            "garnish":      recipe.get("garnish", []),
            "base_spirit":  derive_base_spirit(recipe),
            "family":       derive_family(recipe),
            "flavor_vector": flavor_vec.tolist(),
        }

    # ── Strategy: BLEND ─────────────────────────────────────────────────────
    print("  [1/4] BLEND …")
    blend_vecs = np.array([blend_vector(recipes[n]) for n in recipe_names])
    blend_2d   = run_umap(blend_vecs)
    blend_nn   = nearest_neighbors(recipe_names, blend_vecs)

    # ── Strategy: BLEND+STRUCT — AlignedUMAP over 21 alpha steps ────────────
    # AlignedUMAP jointly optimises all 21 embeddings simultaneously with an
    # alignment penalty between adjacent steps, guaranteeing that each frame
    # can't arbitrarily rotate or flip relative to its neighbours.  Each frame
    # is a genuine UMAP embedding (not a lerp), so clusters are preserved
    # throughout the transition.
    alpha_values = [round(a * 0.05, 2) for a in range(21)]  # 0.00, 0.05, …, 1.00

    print(f"  [2/4] BLEND+STRUCT AlignedUMAP ({len(alpha_values)} steps) …")

    # One feature matrix per alpha — interpolate in vector space
    bs_datasets = [
        np.array([blend_struct_vector(recipes[rn], alpha) for rn in recipe_names])
        for alpha in alpha_values
    ]

    # Every step has the same 100 points: identity relation
    identity = {i: i for i in range(n)}
    relations = [identity] * (len(alpha_values) - 1)

    aligned_mapper = AlignedUMAP(
        n_neighbors=10,
        n_components=2,
        metric="cosine",
        min_dist=0.1,
        alignment_regularisation=0.01,  # strong enough to prevent flips, loose
        alignment_window_size=3,        # look ±1 step when aligning
        random_state=42,
    ).fit(bs_datasets, relations=relations)

    aligned_embeddings = aligned_mapper.embeddings_  # list of 21 (n, 2) arrays

    blend_struct_strategies = {}
    for idx, alpha in enumerate(alpha_values):
        label = f"blend_struct_a{int(round(alpha * 100)):03d}"
        emb_2d = aligned_embeddings[idx]
        bs_vecs = bs_datasets[idx]
        bs_nn   = nearest_neighbors(recipe_names, bs_vecs)
        blend_struct_strategies[label] = {
            "description": (
                f"Taste + structure (α={alpha:.2f}). "
                "Each frame is a genuine UMAP embedding jointly optimised across "
                "all 21 α steps via AlignedUMAP, so clusters persist smoothly "
                "as the slider moves."
            ),
            "alpha": alpha,
            "points": {
                recipe_names[i]: {"x": float(emb_2d[i, 0]), "y": float(emb_2d[i, 1])}
                for i in range(n)
            },
            "neighbors": bs_nn,
        }

    # Default BLEND+STRUCT is α=0.50
    blend_struct_default = blend_struct_strategies["blend_struct_a050"]

    # ── Strategy: ROLE-SLOT ──────────────────────────────────────────────────
    print("  [3/4] ROLE-SLOT …")
    rs_vecs = np.array([role_slot_vector(recipes[n]) for n in recipe_names])
    rs_2d   = run_umap(rs_vecs)
    rs_nn   = nearest_neighbors(recipe_names, rs_vecs)

    # ── Strategy: PERCEPTUAL ─────────────────────────────────────────────────
    print("  [4/4] PERCEPTUAL …")
    perc_vecs = np.array([perceptual_vector(recipes[n]) for n in recipe_names])
    perc_2d   = run_umap(perc_vecs)
    perc_nn   = nearest_neighbors(recipe_names, perc_vecs)

    # ── Assemble output ──────────────────────────────────────────────────────
    output = {
        "strategies": {
            "blend": {
                "description": "Proportion-weighted flavor blend. Pure taste, no structure.",
                "points": {
                    recipe_names[i]: {"x": float(blend_2d[i, 0]), "y": float(blend_2d[i, 1])}
                    for i in range(n)
                },
                "neighbors": blend_nn,
            },
            "blend_struct": blend_struct_default,
            "role_slot": {
                "description": (
                    "Role-slot vectors (4×15=60 dims). "
                    "Compares base-to-base, modifier-to-modifier. "
                    "Two drinks are close only if the same slots taste similar."
                ),
                "points": {
                    recipe_names[i]: {"x": float(rs_2d[i, 0]), "y": float(rs_2d[i, 1])}
                    for i in range(n)
                },
                "neighbors": rs_nn,
            },
            "perceptual": {
                "description": (
                    f"Perceptual blend (punch_weight={PUNCH_WEIGHT}). "
                    "Punchy ingredients win. Small amounts of Chartreuse, Fernet, Mezcal "
                    "pull their slot's character toward theirs."
                ),
                "points": {
                    recipe_names[i]: {"x": float(perc_2d[i, 0]), "y": float(perc_2d[i, 1])}
                    for i in range(n)
                },
                "neighbors": perc_nn,
            },
            # Pre-baked α/β snapshots for blend+struct slider
            **blend_struct_strategies,
        },
        "recipes": recipe_meta,
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {OUTPUT}")
    print(f"  {n} cocktails × 4 strategies (+ 5 α/β snapshots)")


if __name__ == "__main__":
    main()
