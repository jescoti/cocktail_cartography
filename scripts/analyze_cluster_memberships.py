#!/usr/bin/env python3
"""
Analyze cluster memberships from the clustering results to provide accurate naming
"""
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter

def load_embeddings():
    """Load embeddings to get cocktail metadata"""
    with open('data/embeddings.json', 'r') as f:
        data = json.load(f)
    return data['recipes']

def load_clustering_results():
    """Load the clustering results"""
    results = {}

    # Load alpha spectrum results
    alpha_path = Path('viz/clustering_exploration/alpha_spectrum_results.json')
    if alpha_path.exists():
        with open(alpha_path, 'r') as f:
            results['alpha'] = json.load(f)

    # Load tau spectrum results
    tau_path = Path('viz/clustering_exploration/tau_spectrum_results.json')
    if tau_path.exists():
        with open(tau_path, 'r') as f:
            results['tau'] = json.load(f)

    return results

def analyze_cluster_composition(members, recipes):
    """Analyze what's actually in a cluster"""
    analysis = {
        'size': len(members),
        'members': members,
        'base_spirits': Counter(),
        'families': Counter(),
        'methods': Counter(),
        'served': Counter(),
        'common_ingredients': Counter(),
        'has_citrus': 0,
        'has_sugar': 0,
        'has_bitters': 0,
        'has_vermouth': 0,
        'has_liqueur': 0
    }

    all_ingredients = []

    for cocktail_name in members:
        if cocktail_name not in recipes:
            continue

        recipe = recipes[cocktail_name]

        # Count base spirits
        if 'base_spirit' in recipe:
            analysis['base_spirits'][recipe['base_spirit']] += 1

        # Count families
        if 'family' in recipe:
            analysis['families'][recipe['family']] += 1

        # Count methods
        if 'method' in recipe:
            analysis['methods'][recipe['method']] += 1

        # Count served style
        if 'served' in recipe:
            analysis['served'][recipe['served']] += 1

        # Analyze ingredients
        for component in recipe.get('components', []):
            ingredient = component['ingredient']
            all_ingredients.append(ingredient)

            # Check for common ingredient types
            if 'lemon' in ingredient or 'lime' in ingredient or 'grapefruit' in ingredient:
                analysis['has_citrus'] += 1
            if 'sugar' in ingredient or 'simple' in ingredient or 'honey' in ingredient or 'agave' in ingredient:
                analysis['has_sugar'] += 1
            if 'bitters' in ingredient:
                analysis['has_bitters'] += 1
            if 'vermouth' in ingredient:
                analysis['has_vermouth'] += 1
            if 'liqueur' in ingredient or 'maraschino' in ingredient or 'cointreau' in ingredient or 'chartreuse' in ingredient:
                analysis['has_liqueur'] += 1

    # Get most common ingredients
    analysis['common_ingredients'] = Counter(all_ingredients).most_common(10)

    return analysis

def suggest_cluster_name(analysis):
    """Suggest a name based on the cluster analysis"""
    size = analysis['size']
    spirits = analysis['base_spirits']
    families = analysis['families']
    methods = analysis['methods']

    # Get dominant characteristics
    dominant_spirit = spirits.most_common(1)[0][0] if spirits else None
    dominant_family = families.most_common(1)[0][0] if families else None
    dominant_method = methods.most_common(1)[0][0] if methods else None

    citrus_ratio = analysis['has_citrus'] / size if size > 0 else 0
    sugar_ratio = analysis['has_sugar'] / size if size > 0 else 0

    # Generate name based on characteristics
    if dominant_family == 'sour' and citrus_ratio > 0.7:
        if dominant_spirit:
            return f"{dominant_spirit.title()} Sours"
        return "Classic Sours"

    if dominant_family == 'spirit_forward':
        if analysis['has_vermouth'] > size * 0.6:
            return "Manhattan & Martini Family"
        return "Spirit-Forward Classics"

    if dominant_method == 'stirred' and analysis['has_bitters'] > size * 0.5:
        return "Stirred & Bitter"

    if analysis['has_liqueur'] > size * 0.6:
        return "Liqueur-Enhanced"

    if dominant_spirit:
        spirit_ratio = spirits[dominant_spirit] / size
        if spirit_ratio > 0.6:
            return f"{dominant_spirit.title()}-Based"

    # Fallback to family or method
    if dominant_family:
        return f"{dominant_family.replace('_', ' ').title()}"

    if dominant_method:
        return f"{dominant_method.title()} Cocktails"

    return "Mixed Cocktails"

def print_cluster_analysis(name, cluster_data, recipes):
    """Print detailed analysis of a cluster"""
    print(f"\n{'='*60}")
    print(f"Cluster: {name}")
    print('='*60)

    members = cluster_data.get('members', cluster_data.get('all_members', []))
    if not members:
        print("No members found")
        return

    analysis = analyze_cluster_composition(members, recipes)

    print(f"Size: {analysis['size']} cocktails")
    print(f"Members: {', '.join(members[:10])}")
    if len(members) > 10:
        print(f"         ... and {len(members) - 10} more")

    print(f"\nBase Spirits:")
    for spirit, count in analysis['base_spirits'].most_common():
        print(f"  {spirit}: {count} ({count*100//analysis['size']}%)")

    print(f"\nFamilies:")
    for family, count in analysis['families'].most_common():
        print(f"  {family}: {count} ({count*100//analysis['size']}%)")

    print(f"\nMethods:")
    for method, count in analysis['methods'].most_common():
        print(f"  {method}: {count} ({count*100//analysis['size']}%)")

    print(f"\nCharacteristics:")
    print(f"  Has citrus: {analysis['has_citrus']} ({analysis['has_citrus']*100//analysis['size']}%)")
    print(f"  Has sugar: {analysis['has_sugar']} ({analysis['has_sugar']*100//analysis['size']}%)")
    print(f"  Has bitters: {analysis['has_bitters']} ({analysis['has_bitters']*100//analysis['size']}%)")
    print(f"  Has vermouth: {analysis['has_vermouth']} ({analysis['has_vermouth']*100//analysis['size']}%)")

    print(f"\nTop Ingredients:")
    for ingredient, count in analysis['common_ingredients'][:5]:
        print(f"  {ingredient}: {count}")

    suggested_name = suggest_cluster_name(analysis)
    print(f"\nSuggested Name: {suggested_name}")

def main():
    recipes = load_embeddings()
    results = load_clustering_results()

    # Analyze alpha=0 k=8 clustering (the key finding)
    print("\n" + "="*80)
    print("ALPHA=0 K-MEANS K=8 ANALYSIS (Key Finding)")
    print("="*80)

    if 'alpha' in results and 'alpha_0.00' in results['alpha']:
        alpha0 = results['alpha']['alpha_0.00']
        if 'algorithms' in alpha0 and 'kmeans' in alpha0['algorithms']:
            kmeans = alpha0['algorithms']['kmeans']
            if 'results' in kmeans and 'k=8' in kmeans['results']:
                k8_data = kmeans['results']['k=8']
                if 'analysis' in k8_data and 'clusters' in k8_data['analysis']:
                    clusters = k8_data['analysis']['clusters']

                    for cluster_id, cluster_data in sorted(clusters.items(), key=lambda x: x[0]):
                        print_cluster_analysis(f"Cluster {cluster_id}", cluster_data, recipes)

    # Look for the whiskey sour island at tau=4.019
    print("\n" + "="*80)
    print("TAU=4.019 ANALYSIS (Whiskey Sour Island)")
    print("="*80)

    if 'tau' in results and 'tau_4.019' in results['tau']:
        tau4 = results['tau']['tau_4.019']
        print(f"Description: {tau4.get('description', 'N/A')}")
        # Need to find where the actual cluster members are stored
        # The structure seems different from alpha spectrum

if __name__ == "__main__":
    main()