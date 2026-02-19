"""
Analyze how cocktails cluster at different tau values.
Find drinks that migrate between clusters as tau changes.
"""

import json
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from collections import defaultdict

# Load data
DATA_PATH = Path(__file__).parent.parent / "data"
with open(DATA_PATH / "embeddings.json", "r") as f:
    data = json.load(f)

with open(DATA_PATH / "recipes.json", "r") as f:
    recipes = json.load(f)

# Get tau strategies
tau_strategies = data["strategies"]["tau"]
tau_values = sorted([float(k) for k in tau_strategies.keys()])

print(f"Analyzing {len(tau_values)} tau values: {tau_values[:3]}...{tau_values[-3:]}")

# Helper to get embedding array for a tau value
def get_embedding_array(tau):
    tau_key = str(tau)
    points = tau_strategies[tau_key]["embedding"]
    names = sorted(points.keys())
    coords = np.array([[points[n]["x"], points[n]["y"]] for n in names])
    return names, coords

# Cluster at each tau value
n_clusters = 8  # reasonable number for ~100 cocktails
cluster_assignments = {}

for tau in tau_values:
    names, coords = get_embedding_array(tau)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords)
    cluster_assignments[tau] = {name: label for name, label in zip(names, labels)}

# Find drinks that change clusters dramatically
print("\n" + "="*80)
print("COCKTAILS THAT MIGRATE BETWEEN CLUSTERS")
print("="*80)

# Track migrations for specific interesting tau transitions
# Use actual tau values from our data
actual_taus = tau_values
low_tau = actual_taus[0]  # 0.1
early_tau = actual_taus[4]  # ~0.336
mid_tau = actual_taus[10]  # ~2.069
late_tau = actual_taus[16]  # ~12.7
high_tau = actual_taus[-1]  # ~31.6

transitions = [
    (low_tau, early_tau, f"From max-pooling to early blend"),
    (early_tau, mid_tau, f"From early blend to balanced"),
    (mid_tau, late_tau, f"From balanced to volume-weighted"),
    (late_tau, high_tau, f"From volume-weighted to uniform"),
    (low_tau, high_tau, f"Full range: max to uniform")
]

migration_stories = defaultdict(list)

for tau_low, tau_high, description in transitions:
    print(f"\n{description} (τ={tau_low} → τ={tau_high}):")
    print("-" * 50)

    migrations = []
    for name in cluster_assignments[tau_low].keys():
        cluster_before = cluster_assignments[tau_low][name]
        cluster_after = cluster_assignments[tau_high][name]
        if cluster_before != cluster_after:
            migrations.append(name)
            migration_stories[name].append(f"τ={tau_low}→{tau_high}")

    print(f"  {len(migrations)} drinks changed clusters")

    # Show some interesting examples
    if migrations:
        # Focus on drinks with intense ingredients
        intense_drinks = []
        for drink in migrations[:20]:
            recipe = recipes.get(drink, {})
            components = recipe.get("components", [])
            has_intense = any(
                any(keyword in comp.get("ingredient", "").lower()
                    for keyword in ["fernet", "chartreuse", "mezcal", "islay", "absinthe",
                                  "campari", "aperol", "cynar", "amaro", "maraschino"])
                for comp in components
            )
            if has_intense:
                intense_drinks.append(drink)

        if intense_drinks:
            print(f"  Drinks with intense ingredients that moved:")
            for drink in intense_drinks[:8]:
                print(f"    - {drink}")

# Find drinks that move the most
print("\n" + "="*80)
print("MOST MOBILE COCKTAILS (across all tau values)")
print("="*80)

mobility_scores = {}
names = list(cluster_assignments[tau_values[0]].keys())

for name in names:
    clusters_visited = set()
    for tau in tau_values:
        clusters_visited.add(cluster_assignments[tau][name])
    mobility_scores[name] = len(clusters_visited)

# Sort by mobility
most_mobile = sorted(mobility_scores.items(), key=lambda x: x[1], reverse=True)

print("\nDrinks that visit the most different clusters:")
for drink, n_clusters_visited in most_mobile[:15]:
    recipe = recipes.get(drink, {})
    components = recipe.get("components", [])

    # Get key ingredients
    ingredients = []
    for comp in components[:3]:  # First 3 components
        ing_name = comp.get("ingredient", "")
        ml = comp.get("ml")
        if ml:
            ingredients.append(f"{ing_name} ({ml}ml)")
        else:
            ingredients.append(ing_name)

    print(f"  {drink} ({n_clusters_visited} clusters): {', '.join(ingredients)}")

# Analyze specific cluster formations at key tau values
print("\n" + "="*80)
print("CLUSTER CHARACTERISTICS AT KEY TAU VALUES")
print("="*80)

key_taus = [low_tau, early_tau, mid_tau, late_tau, high_tau]

for tau in key_taus:
    print(f"\nτ = {tau}:")
    print("-" * 30)

    # Group drinks by cluster
    clusters = defaultdict(list)
    for name, cluster_id in cluster_assignments[tau].items():
        clusters[cluster_id].append(name)

    # Analyze each cluster
    for cluster_id in sorted(clusters.keys()):
        members = clusters[cluster_id]
        if len(members) < 3:
            continue

        print(f"\n  Cluster {cluster_id} ({len(members)} drinks):")

        # Find common characteristics
        base_spirits = defaultdict(int)
        has_citrus = 0
        has_bitter = 0
        has_sweet_liqueur = 0
        intense_ingredients = defaultdict(int)

        for drink in members:
            recipe = recipes.get(drink, {})

            # Count base spirits
            for comp in recipe.get("components", []):
                ing = comp.get("ingredient", "").lower()
                ml = comp.get("ml", 0)

                if ml and ml > 20:  # Significant volume
                    if "whiskey" in ing or "bourbon" in ing or "rye" in ing:
                        base_spirits["whiskey"] += 1
                    elif "gin" in ing:
                        base_spirits["gin"] += 1
                    elif "rum" in ing:
                        base_spirits["rum"] += 1
                    elif "tequila" in ing or "mezcal" in ing:
                        base_spirits["agave"] += 1
                    elif "vodka" in ing:
                        base_spirits["vodka"] += 1
                    elif "brandy" in ing or "cognac" in ing:
                        base_spirits["brandy"] += 1

                # Check for citrus
                if comp.get("role") == "citrus":
                    has_citrus += 1

                # Check for bitter/intense ingredients
                if any(b in ing for b in ["campari", "aperol", "fernet", "cynar", "amaro"]):
                    has_bitter += 1
                    intense_ingredients[ing] += 1

                # Check for sweet liqueurs
                if any(s in ing for s in ["chartreuse", "maraschino", "benedictine", "cointreau", "triple sec"]):
                    has_sweet_liqueur += 1
                    intense_ingredients[ing] += 1

        # Report characteristics
        if base_spirits:
            top_spirit = max(base_spirits.items(), key=lambda x: x[1])
            print(f"    Primary spirit: {top_spirit[0]} ({top_spirit[1]}/{len(members)} drinks)")

        if has_citrus > len(members) * 0.5:
            print(f"    Citrus-forward ({has_citrus}/{len(members)} have citrus)")

        if has_bitter > len(members) * 0.3:
            print(f"    Bitter/Amaro cluster ({has_bitter}/{len(members)} have bitter components)")

        if intense_ingredients:
            top_intense = sorted(intense_ingredients.items(), key=lambda x: x[1], reverse=True)[:2]
            print(f"    Key intense ingredients: {', '.join([f'{k} ({v})' for k, v in top_intense])}")

        # Show example members
        print(f"    Examples: {', '.join(members[:5])}")

# Find drinks that stay together vs drift apart
print("\n" + "="*80)
print("STABLE PAIRS VS DRIFTING PAIRS")
print("="*80)

def euclidean_distance(name1, name2, tau):
    _, coords = get_embedding_array(tau)
    names = sorted(tau_strategies[str(tau)]["embedding"].keys())
    idx1 = names.index(name1)
    idx2 = names.index(name2)
    return np.linalg.norm(coords[idx1] - coords[idx2])

# Check some interesting pairs
pairs_to_check = [
    ("Negroni", "Boulevardier"),  # Both bitter, different base
    ("Margarita", "Daiquiri"),  # Both citrus sours, different base
    ("Manhattan", "Martini"),  # Both spirit-forward, different profiles
    ("Penicillin", "Gold Rush"),  # Both whiskey sours, one has smoke
    ("Paper Plane", "Last Word"),  # Both equal parts, intense ingredients
    ("Aperol Spritz", "Americano"),  # Both have Aperol/Campari
    ("Bee's Knees", "Gimlet"),  # Both gin sours
    ("Old Fashioned", "Sazerac"),  # Both whiskey old fashioneds
    ("Mai Tai", "Painkiller"),  # Both tiki rum
]

print("\nHow drink pairs move together or apart:")
for name1, name2 in pairs_to_check:
    if name1 in names and name2 in names:
        dist_low = euclidean_distance(name1, name2, low_tau)
        dist_high = euclidean_distance(name1, name2, high_tau)
        change = dist_high - dist_low

        if abs(change) > 0.5:  # Significant change
            direction = "DRIFT APART" if change > 0 else "COME TOGETHER"
            print(f"  {name1} & {name2}: {direction} (Δ = {change:.2f})")
            print(f"    Distance at τ=0.1: {dist_low:.2f}, at τ=31.6: {dist_high:.2f}")