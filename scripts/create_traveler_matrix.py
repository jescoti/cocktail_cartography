#!/usr/bin/env python3
"""
Create a traveler matrix showing how cocktails move between clusters
under different vectorization strategies.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import seaborn as sns

# Load the enhanced cluster analysis
with open('viz/enhanced_cluster_analysis.json', 'r') as f:
    results = json.load(f)

# Load embeddings for cocktail names
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

# Focus on notable cocktails that are interesting to track
notable_cocktails = [
    'boulevardier', 'penicillin', 'last_word', 'paper_plane',
    'bees_knees', 'aperol_spritz', 'mai_tai', 'whiskey_sour',
    'negroni', 'manhattan', 'old_fashioned', 'martini',
    'daiquiri', 'margarita', 'mojito', 'aviation',
    'sazerac', 'ramos_gin_fizz', 'french_75', 'dark_and_stormy'
]

# Strategy order for display
strategy_order = [
    'blend',
    'blend_struct_a025',
    'blend_struct_a050',
    'blend_struct_a075',
    'blend_struct_a100',
    'role_slot',
    'perceptual'
]

# Create a matrix showing which cocktails cluster together
def find_cluster_companions(cocktail_name, strategy_key, results):
    """Find which cocktails cluster with a given cocktail in a strategy."""
    if strategy_key not in results:
        return []

    clusters = results[strategy_key]['clusters']
    for cluster_id, members in clusters.items():
        if cocktail_name in members:
            # Return other members (not including the cocktail itself)
            return [m for m in members if m != cocktail_name]

    return []

# Build companion matrix for each notable cocktail
print("Analyzing cocktail companions across strategies...")
print("="*60)

companion_data = {}
for cocktail in notable_cocktails:
    # Check which key exists for the strategy data
    blend_data = data['strategies']['blend']
    cocktail_data = blend_data.get('points') or blend_data.get('projects', {})
    if cocktail not in cocktail_data:
        continue

    companion_data[cocktail] = {}
    print(f"\n{cocktail.replace('_', ' ').title()}:")

    for strategy in strategy_order:
        if strategy not in results:
            continue

        companions = find_cluster_companions(cocktail, strategy, results)
        companion_data[cocktail][strategy] = companions

        # Find interesting companions (other notable cocktails)
        notable_companions = [c for c in companions if c in notable_cocktails]
        if notable_companions:
            strategy_name = results[strategy].get('title', strategy)
            print(f"  {strategy_name}: with {', '.join(notable_companions[:3])}...")

# Create a "who clusters with whom" matrix
print("\n" + "="*60)
print("Creating companion frequency matrix...")

# Count how often each pair clusters together
pair_counts = defaultdict(int)
for cocktail1 in notable_cocktails:
    if cocktail1 not in companion_data:
        continue

    for strategy, companions in companion_data[cocktail1].items():
        for cocktail2 in companions:
            if cocktail2 in notable_cocktails:
                # Create sorted pair to avoid duplicates
                pair = tuple(sorted([cocktail1, cocktail2]))
                pair_counts[pair] += 1

# Convert to matrix
n = len(notable_cocktails)
matrix = np.zeros((n, n))
cocktail_indices = {c: i for i, c in enumerate(notable_cocktails)}

for (c1, c2), count in pair_counts.items():
    if c1 in cocktail_indices and c2 in cocktail_indices:
        i, j = cocktail_indices[c1], cocktail_indices[c2]
        matrix[i, j] = count
        matrix[j, i] = count  # Symmetric

# Normalize by number of strategies
matrix = matrix / len(strategy_order)

# Create visualization with better spacing
fig = plt.figure(figsize=(24, 12))
fig.patch.set_facecolor('#1a1a1d')

# Create subplot for heatmap with more space for labels
ax1 = plt.subplot(1, 2, 1)

# Format cocktail names properly
def format_cocktail_name(name):
    """Format cocktail names with proper capitalization."""
    special_cases = {
        'bees_knees': "Bee's Knees",
        'dark_and_stormy': 'Dark & Stormy',
        'french_75': 'French 75',
        'mai_tai': 'Mai Tai',
        'old_fashioned': 'Old Fashioned',
        'whiskey_sour': 'Whiskey Sour',
        'paper_plane': 'Paper Plane',
        'last_word': 'Last Word',
        'aperol_spritz': 'Aperol Spritz',
        'ramos_gin_fizz': 'Ramos Gin Fizz'
    }
    if name in special_cases:
        return special_cases[name]
    return name.replace('_', ' ').title()

formatted_labels = [format_cocktail_name(c) for c in notable_cocktails]

# Create heatmap with better label handling
im = ax1.imshow(matrix, cmap='YlOrRd', aspect='equal', vmin=0, vmax=1)

# Set ticks and labels
ax1.set_xticks(np.arange(len(notable_cocktails)))
ax1.set_yticks(np.arange(len(notable_cocktails)))
ax1.set_xticklabels(formatted_labels, rotation=45, ha='right', fontsize=10)
ax1.set_yticklabels(formatted_labels, fontsize=10)

# Add colorbar
cbar = plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
cbar.set_label('Frequency of Clustering Together', rotation=270, labelpad=20, color='#C5C5B0')
cbar.ax.tick_params(colors='#C5C5B0')

# Add grid for better readability
ax1.set_xticks(np.arange(len(notable_cocktails))-.5, minor=True)
ax1.set_yticks(np.arange(len(notable_cocktails))-.5, minor=True)
ax1.grid(which='minor', color='#2a2a2d', linewidth=0.5)

ax1.set_title('Cocktail Companion Matrix\n(How often cocktails cluster together across strategies)',
             fontsize=14, color='#D4AF37', weight='bold', pad=20)
ax1.tick_params(colors='#C5C5B0')

# Create second subplot for insights
ax2 = plt.subplot(1, 2, 2)

# Create a movement tracking visualization
# Track specific interesting movements
movements = {
    'Boulevardier': {
        'Flavor-based': ['Old Fashioned', 'Manhattan'],
        'Structure-based': ['Negroni'],
        'Insight': 'Whiskey heart, Negroni structure'
    },
    'Penicillin': {
        'Without intensity': ['Whiskey Sour'],
        'With intensity': ['Old Fashioned'],
        'Insight': 'Islay float changes perception'
    },
    'Last Word': {
        'Flavor-based': ['Paper Plane', 'Aviation'],
        'Structure-based': ['Daiquiri', 'Margarita'],
        'Insight': 'Chartreuse bridges categories'
    },
    'Aperol Spritz': {
        'Low structure weight': ['Margarita'],
        'High structure weight': ['Negroni'],
        'Insight': 'Aperol links to bitter family'
    }
}

# Text summary on second subplot
ax2.axis('off')
ax2.set_facecolor('#1a1a1d')

y_pos = 0.95
for cocktail, movement in movements.items():
    text = f"**{cocktail}**\n"

    for context, companions in list(movement.items())[:-1]:  # Skip 'Insight'
        text += f"  {context}: {', '.join(companions)}\n"

    text += f"  → {movement['Insight']}\n\n"

    ax2.text(0.05, y_pos, text, transform=ax2.transAxes,
            fontsize=11, color='#C5C5B0', verticalalignment='top',
            family='monospace')

    y_pos -= 0.23

ax2.set_title('Key Traveler Insights',
             fontsize=14, color='#D4AF37', weight='bold',
             transform=ax2.transAxes, x=0.5, y=0.98)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Leave space for labels
plt.savefig('viz/traveler_matrix.svg', dpi=150, facecolor='#1a1a1d', bbox_inches='tight')
plt.close()

print(f"\nTraveler matrix saved to viz/traveler_matrix.svg")

# Generate detailed traveler report
print("\n" + "="*60)
print("DETAILED TRAVELER ANALYSIS")
print("="*60)

# Find cocktails that are most stable (cluster with same companions)
stability_scores = {}
for cocktail in notable_cocktails:
    if cocktail not in companion_data:
        continue

    # Check consistency of companions
    all_companions = set()
    companion_sets = []

    for strategy, companions in companion_data[cocktail].items():
        notable_companions = set(c for c in companions if c in notable_cocktails)
        companion_sets.append(notable_companions)
        all_companions.update(notable_companions)

    if len(companion_sets) > 1 and all_companions:
        # Calculate Jaccard similarity between strategy companion sets
        similarities = []
        for i in range(len(companion_sets)-1):
            if companion_sets[i] and companion_sets[i+1]:
                intersection = companion_sets[i] & companion_sets[i+1]
                union = companion_sets[i] | companion_sets[i+1]
                similarity = len(intersection) / len(union) if union else 0
                similarities.append(similarity)

        if similarities:
            stability_scores[cocktail] = np.mean(similarities)

# Report stable vs traveler cocktails
stable_cocktails = sorted([(s, c) for c, s in stability_scores.items() if s > 0.5],
                         reverse=True)
traveler_cocktails = sorted([(s, c) for c, s in stability_scores.items() if s < 0.3])

print("\nMost Stable Cocktails (consistent companions):")
for score, cocktail in stable_cocktails[:5]:
    print(f"  {cocktail.replace('_', ' ').title()}: {score:.2f} stability score")

print("\nMost Nomadic Cocktails (changing companions):")
for score, cocktail in traveler_cocktails[:5]:
    print(f"  {cocktail.replace('_', ' ').title()}: {score:.2f} stability score")

# Save detailed results
with open('viz/traveler_analysis.json', 'w') as f:
    json.dump({
        'companion_data': companion_data,
        'stability_scores': stability_scores,
        'pair_counts': {f"{k[0]}_{k[1]}": v for k, v in pair_counts.items()},
        'movements': movements
    }, f, indent=2)

print("\nDetailed analysis saved to viz/traveler_analysis.json")
print("="*60)