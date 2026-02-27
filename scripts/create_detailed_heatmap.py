#!/usr/bin/env python3
"""
Create a detailed, annotated heatmap showing cocktail clustering relationships.
This version adds value annotations and better formatting for readability.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.patches as mpatches

# Load the enhanced cluster analysis
with open('viz/enhanced_cluster_analysis.json', 'r') as f:
    results = json.load(f)

# Load embeddings for cocktail names
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

# Focus on key cocktails for a cleaner view
key_cocktails = [
    'boulevardier', 'negroni', 'old_fashioned', 'manhattan',
    'whiskey_sour', 'penicillin',
    'martini', 'martinez',
    'last_word', 'paper_plane', 'aviation',
    'margarita', 'daiquiri', 'mojito',
    'bees_knees', 'aperol_spritz'
]

# Strategy order for analysis
strategy_order = [
    'blend',
    'blend_struct_a050',
    'role_slot',
    'perceptual'
]

def format_cocktail_name(name):
    """Format cocktail names with proper capitalization."""
    special_cases = {
        'bees_knees': "Bee's Knees",
        'old_fashioned': 'Old Fashioned',
        'whiskey_sour': 'Whiskey Sour',
        'paper_plane': 'Paper Plane',
        'last_word': 'Last Word',
        'aperol_spritz': 'Aperol Spritz'
    }
    if name in special_cases:
        return special_cases[name]
    return name.replace('_', ' ').title()

# Find cluster companions
def find_cluster_companions(cocktail_name, strategy_key, results):
    """Find which cocktails cluster with a given cocktail in a strategy."""
    if strategy_key not in results:
        return []

    clusters = results[strategy_key]['clusters']
    for cluster_id, members in clusters.items():
        if cocktail_name in members:
            return [m for m in members if m != cocktail_name]

    return []

# Build companion data
companion_data = {}
for cocktail in key_cocktails:
    # Check if cocktail exists
    blend_data = data['strategies']['blend']
    cocktail_data = blend_data.get('points') or blend_data.get('projects', {})
    if cocktail not in cocktail_data:
        continue

    companion_data[cocktail] = {}
    for strategy in strategy_order:
        if strategy not in results:
            continue
        companions = find_cluster_companions(cocktail, strategy, results)
        companion_data[cocktail][strategy] = companions

# Count co-clustering frequency
pair_counts = defaultdict(int)
for cocktail1 in key_cocktails:
    if cocktail1 not in companion_data:
        continue

    for strategy, companions in companion_data[cocktail1].items():
        for cocktail2 in companions:
            if cocktail2 in key_cocktails:
                pair = tuple(sorted([cocktail1, cocktail2]))
                pair_counts[pair] += 1

# Convert to matrix
n = len(key_cocktails)
matrix = np.zeros((n, n))
cocktail_indices = {c: i for i, c in enumerate(key_cocktails)}

for (c1, c2), count in pair_counts.items():
    if c1 in cocktail_indices and c2 in cocktail_indices:
        i, j = cocktail_indices[c1], cocktail_indices[c2]
        matrix[i, j] = count
        matrix[j, i] = count

# Create figure with better proportions
fig, ax = plt.subplots(figsize=(14, 12))
fig.patch.set_facecolor('#1a1a1d')
ax.set_facecolor('#1a1a1d')

# Create custom colormap
from matplotlib.colors import LinearSegmentedColormap
colors_list = ['#1a1a1d', '#4a4a3d', '#8B7355', '#CD9B1D', '#FFD700']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('custom', colors_list, N=n_bins)

# Plot heatmap
im = ax.imshow(matrix, cmap=cmap, aspect='equal', vmin=0, vmax=len(strategy_order))

# Set ticks and labels
formatted_labels = [format_cocktail_name(c) for c in key_cocktails]
ax.set_xticks(np.arange(len(key_cocktails)))
ax.set_yticks(np.arange(len(key_cocktails)))
ax.set_xticklabels(formatted_labels, rotation=45, ha='right', fontsize=11, color='#C5C5B0')
ax.set_yticklabels(formatted_labels, fontsize=11, color='#C5C5B0')

# Add value annotations
for i in range(len(key_cocktails)):
    for j in range(len(key_cocktails)):
        if i != j:  # Don't annotate diagonal
            value = int(matrix[i, j])
            if value > 0:
                # Color based on value
                text_color = '#1a1a1d' if value >= 3 else '#C5C5B0'
                ax.text(j, i, str(value), ha='center', va='center',
                       color=text_color, fontsize=9, fontweight='bold')

# Add grid for clarity
ax.set_xticks(np.arange(len(key_cocktails))-.5, minor=True)
ax.set_yticks(np.arange(len(key_cocktails))-.5, minor=True)
ax.grid(which='minor', color='#4a4a3d', linewidth=0.8)
ax.tick_params(which='minor', size=0)

# Title and labels
ax.set_title('Cocktail Clustering Frequency Matrix\nHow many strategies group these cocktails together',
            fontsize=16, color='#D4AF37', weight='bold', pad=20)

# Add colorbar with custom formatting
cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Number of Strategies\nGrouping Together', rotation=270, labelpad=25,
              color='#C5C5B0', fontsize=11)
cbar.ax.tick_params(colors='#C5C5B0')
cbar.set_ticks([0, 1, 2, 3, 4])
cbar.set_ticklabels(['Never', '1 Strategy', '2 Strategies', '3 Strategies', 'All 4'])

# Add legend explaining what this means
legend_text = [
    "Reading this matrix:",
    "• 4 = Always cluster together (stable companions)",
    "• 3 = Usually cluster together",
    "• 2 = Sometimes cluster together",
    "• 1 = Rarely cluster together",
    "• 0 = Never cluster together"
]

# Add text box with legend
props = dict(boxstyle='round', facecolor='#2d2d30', alpha=0.9, edgecolor='#4a4a3d')
legend_str = '\n'.join(legend_text)
ax.text(0.02, 0.98, legend_str, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=props, color='#C5C5B0')

# Highlight interesting patterns with rectangles
# Whiskey family box
whiskey_indices = [cocktail_indices[c] for c in ['boulevardier', 'old_fashioned', 'manhattan', 'whiskey_sour', 'penicillin']
                  if c in cocktail_indices]
if len(whiskey_indices) >= 2:
    min_idx, max_idx = min(whiskey_indices), max(whiskey_indices)
    rect = mpatches.Rectangle((min_idx-0.45, min_idx-0.45),
                             max_idx-min_idx+0.9, max_idx-min_idx+0.9,
                             linewidth=2, edgecolor='#CD9B1D', facecolor='none',
                             linestyle='--', alpha=0.6)
    ax.add_patch(rect)
    ax.text(max_idx+0.7, (min_idx+max_idx)/2, 'Whiskey\nFamily',
           fontsize=9, color='#CD9B1D', va='center')

# Citrus/Herbal family box
citrus_indices = [cocktail_indices[c] for c in ['last_word', 'paper_plane', 'aviation', 'margarita', 'daiquiri']
                 if c in cocktail_indices]
if len(citrus_indices) >= 2:
    min_idx, max_idx = min(citrus_indices), max(citrus_indices)
    rect = mpatches.Rectangle((min_idx-0.45, min_idx-0.45),
                             max_idx-min_idx+0.9, max_idx-min_idx+0.9,
                             linewidth=2, edgecolor='#50C878', facecolor='none',
                             linestyle='--', alpha=0.6)
    ax.add_patch(rect)
    ax.text(max_idx+0.7, (min_idx+max_idx)/2, 'Citrus/\nHerbal',
           fontsize=9, color='#50C878', va='center')

plt.tight_layout()
plt.savefig('viz/detailed_heatmap.svg', dpi=150, facecolor='#1a1a1d', bbox_inches='tight')
plt.close()

print("Detailed heatmap saved to viz/detailed_heatmap.svg")

# Create a companion analysis showing which cocktails are most/least connected
connectivity = {}
for cocktail in key_cocktails:
    if cocktail in cocktail_indices:
        idx = cocktail_indices[cocktail]
        # Sum connections (exclude self)
        connections = np.sum(matrix[idx, :]) - matrix[idx, idx]
        connectivity[cocktail] = connections

# Sort by connectivity
sorted_connectivity = sorted(connectivity.items(), key=lambda x: x[1], reverse=True)

print("\n" + "="*60)
print("COCKTAIL CONNECTIVITY ANALYSIS")
print("="*60)
print("\nMost Connected (cluster with many different cocktails):")
for cocktail, score in sorted_connectivity[:5]:
    print(f"  {format_cocktail_name(cocktail)}: {score:.0f} total connections")

print("\nLeast Connected (cluster with few different cocktails):")
for cocktail, score in sorted_connectivity[-5:]:
    print(f"  {format_cocktail_name(cocktail)}: {score:.0f} total connections")

# Identify exclusive pairs (only cluster with each other)
print("\nExclusive Relationships (high mutual clustering):")
threshold = 3  # At least 3 out of 4 strategies
for i, c1 in enumerate(key_cocktails):
    for j, c2 in enumerate(key_cocktails[i+1:], i+1):
        if matrix[i, j] >= threshold:
            # Check if this is a strong mutual relationship
            c1_total = np.sum(matrix[i, :] >= threshold) - 1  # Exclude self
            c2_total = np.sum(matrix[j, :] >= threshold) - 1
            if c1_total <= 3 and c2_total <= 3:  # They don't cluster with many others
                print(f"  {format_cocktail_name(c1)} ↔ {format_cocktail_name(c2)}: {matrix[i,j]:.0f}/4 strategies")

print("="*60)