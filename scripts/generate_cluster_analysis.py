#!/usr/bin/env python3
"""
Generate static cluster analysis visualizations for the analysis.html page.
Creates SVG images showing different clustering strategies with labeled regions.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Ellipse
from scipy.spatial import ConvexHull
from collections import defaultdict
import os

# Load data
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

# Define meaningful clusters for each strategy based on the analysis
CLUSTERS = {
    'blend': {
        'Citrus-Forward Sours': {
            'members': ['daiquiri', 'mojito', 'caipirinha', 'hemingway_daiquiri', 'pisco_sour',
                       'gimlet', 'margarita', 'paloma', 'tommys_margarita', 'gin_sour',
                       'whiskey_sour', 'amaretto_sour'],
            'color': '#50C878',
            'description': 'Refreshing lime/lemon-forward drinks with citrus-sugar balance'
        },
        'Whiskey-Vermouth Territory': {
            'members': ['manhattan', 'perfect_manhattan', 'rob_roy', 'brooklyn',
                       'vieux_carre', 'remember_the_maine', 'greenpoint', 'little_italy',
                       'black_manhattan', 'dry_manhattan'],
            'color': '#CD7F32',
            'description': 'Rye/bourbon + sweet vermouth stirred drinks'
        },
        'Martini Family': {
            'members': ['martini', 'martini_olive', 'fifty_fifty_martini', 'vesper',
                       'gibson', 'tuxedo', 'dirty_martini'],
            'color': '#C0C0C0',
            'description': 'Gin + dry vermouth variations'
        },
        'Bitter Aperitivo': {
            'members': ['negroni', 'boulevardier', 'americano', 'sbagliato',
                       'jungle_bird', 'paper_plane', 'naked_and_famous'],
            'color': '#E0115F',
            'description': 'Campari/Aperol-based bitter-sweet balance'
        },
        'Old Fashioned Territory': {
            'members': ['old_fashioned', 'sazerac', 'improved_whiskey_cocktail',
                       'oaxacan_old_fashioned', 'wisconsin_old_fashioned'],
            'color': '#8B4513',
            'description': 'Spirit-forward with minimal modification'
        },
        'Complex Equal-Parts': {
            'members': ['last_word', 'final_ward', 'corpse_reviver_2'],
            'color': '#0F52BA',
            'description': 'Equal-parts templates with complex flavor profiles'
        }
    },
    'role_slot': {
        'Equal-Parts Templates': {
            'members': ['negroni', 'boulevardier', 'old_pal', 'mezcal_negroni', 'white_negroni',
                       'last_word', 'paper_plane', 'final_ward', 'naked_and_famous',
                       'corpse_reviver_2'],
            'color': '#0F52BA',
            'description': 'Structurally identical equal-parts recipes'
        },
        'Classic Sour Grammar': {
            'members': ['daiquiri', 'whiskey_sour', 'margarita', 'gimlet', 'bees_knees',
                       'southside', 'clover_club', 'pisco_sour', 'gin_sour', 'amaretto_sour',
                       'hemingway_daiquiri', 'aviation', 'white_lady'],
            'color': '#50C878',
            'description': 'Base + citrus + sweetener structure'
        },
        'Spirit-Forward Stirred': {
            'members': ['manhattan', 'rob_roy', 'black_manhattan', 'martinez', 'vieux_carre',
                       'sazerac', 'old_fashioned', 'improved_whiskey_cocktail', 'toronto',
                       'remember_the_maine', 'brooklyn'],
            'color': '#CD7F32',
            'description': 'Base + modifier, minimal citrus'
        },
        'Martini Structure': {
            'members': ['martini', 'martini_olive', 'fifty_fifty_martini', 'gibson',
                       'dirty_martini', 'vesper', 'tuxedo'],
            'color': '#C0C0C0',
            'description': 'Gin base + dry vermouth modifier'
        }
    },
    'perceptual': {
        'Smoky & Intense': {
            'members': ['penicillin', 'mezcal_negroni', 'oaxacan_old_fashioned',
                       'division_bell', 'naked_and_famous', 'mezcal_sour'],
            'color': '#8B4513',
            'description': 'Dominated by smoky mezcal or Islay scotch'
        },
        'Chartreuse Territory': {
            'members': ['last_word', 'final_ward', 'bijou', 'yellow_jacket', 'greenpoint',
                       'champs_elysees'],
            'color': '#7FFF00',
            'description': 'Green Chartreuse intensity dominates'
        },
        'Fernet Forward': {
            'members': ['hanky_panky', 'toronto', 'fanciulli'],
            'color': '#4B0082',
            'description': 'Fernet Branca\'s menthol-bitter intensity'
        },
        'Absinthe-Touched': {
            'members': ['sazerac', 'corpse_reviver_2', 'death_in_the_afternoon',
                       'improved_whiskey_cocktail', 'rattlesnake'],
            'color': '#50C878',
            'description': 'Absinthe rinse or inclusion adds anise notes'
        },
        'Maraschino Sweetness': {
            'members': ['aviation', 'hemingway_daiquiri', 'martinez', 'tuxedo',
                       'last_word', 'casino'],
            'color': '#FFB6C1',
            'description': 'Maraschino liqueur\'s cherry-almond character'
        }
    }
}

def create_visualization(strategy_key, title, output_file):
    """Create a static visualization for a given strategy."""

    fig, ax = plt.subplots(figsize=(14, 10))

    # Set dark background
    fig.patch.set_facecolor('#1a1a1d')
    ax.set_facecolor('#1a1a1d')

    # Get points for this strategy
    points = data['strategies'][strategy_key]['points']
    clusters = CLUSTERS.get(strategy_key, {})

    # Convert to arrays for plotting
    all_names = list(points.keys())
    all_x = [points[name]['x'] for name in all_names]
    all_y = [points[name]['y'] for name in all_names]

    # Create color map for points
    point_colors = []
    point_sizes = []
    for name in all_names:
        in_cluster = False
        for cluster_name, cluster_info in clusters.items():
            if name in cluster_info['members']:
                point_colors.append(cluster_info['color'])
                point_sizes.append(80)
                in_cluster = True
                break
        if not in_cluster:
            point_colors.append('#666666')
            point_sizes.append(40)

    # Draw cluster boundaries first (behind points)
    for cluster_name, cluster_info in clusters.items():
        cluster_points = []
        for member in cluster_info['members']:
            if member in points:
                cluster_points.append([points[member]['x'], points[member]['y']])

        if len(cluster_points) >= 3:
            cluster_points = np.array(cluster_points)

            # Try to create a convex hull
            try:
                hull = ConvexHull(cluster_points)
                hull_points = cluster_points[hull.vertices]

                # Expand hull slightly for visual clarity
                center = np.mean(hull_points, axis=0)
                expanded = []
                for p in hull_points:
                    direction = p - center
                    expanded.append(p + direction * 0.1)
                expanded = np.array(expanded)

                # Draw the boundary
                from matplotlib.patches import Polygon
                poly = Polygon(expanded, alpha=0.15, facecolor=cluster_info['color'],
                             edgecolor=cluster_info['color'], linewidth=2, linestyle='--')
                ax.add_patch(poly)

                # Add cluster label
                ax.text(center[0], center[1], cluster_name.upper(),
                       fontsize=10, color=cluster_info['color'],
                       ha='center', va='center', weight='bold', alpha=0.7)

            except:
                # If hull fails, use a circle around the mean
                center = np.mean(cluster_points, axis=0)
                radius = np.max(np.linalg.norm(cluster_points - center, axis=1)) * 1.2
                circle = plt.Circle(center, radius, alpha=0.1, facecolor=cluster_info['color'],
                                   edgecolor=cluster_info['color'], linewidth=2, linestyle='--')
                ax.add_patch(circle)
                ax.text(center[0], center[1], cluster_name.upper(),
                       fontsize=10, color=cluster_info['color'],
                       ha='center', va='center', weight='bold', alpha=0.7)

    # Plot all points
    ax.scatter(all_x, all_y, c=point_colors, s=point_sizes, alpha=0.8, edgecolors='#F5F5DC', linewidth=0.5)

    # Add labels for notable cocktails
    notable = ['martini', 'manhattan', 'negroni', 'daiquiri', 'old_fashioned', 'margarita',
               'boulevardier', 'last_word', 'penicillin', 'aviation', 'sazerac', 'aperol_spritz',
               'trinidad_sour', 'corpse_reviver_2', 'paper_plane']

    for name in notable:
        if name in points:
            x, y = points[name]['x'], points[name]['y']
            display_name = name.replace('_', ' ').title()
            ax.annotate(display_name, (x, y), xytext=(5, 5),
                       textcoords='offset points', fontsize=8,
                       color='#C5C5B0', alpha=0.8)

    # Style the plot
    ax.set_title(title, fontsize=16, color='#D4AF37', weight='bold', pad=20)
    ax.set_xlabel('UMAP Dimension 1', fontsize=12, color='#C5C5B0')
    ax.set_ylabel('UMAP Dimension 2', fontsize=12, color='#C5C5B0')

    # Remove grid and ticks
    ax.grid(False)
    ax.tick_params(colors='#666666')

    # Set spine colors
    for spine in ax.spines.values():
        spine.set_edgecolor('#4a4a3d')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, facecolor='#1a1a1d', edgecolor='none')
    plt.close()

    return clusters

def generate_comparison_plot():
    """Generate a plot showing how cocktails move between strategies."""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.patch.set_facecolor('#1a1a1d')

    strategies = [
        ('blend', 'Pure Flavor (BLEND)'),
        ('role_slot', 'Recipe Grammar (ROLE-SLOT)'),
        ('perceptual', 'Intensity-Weighted (PERCEPTUAL)'),
        ('blend_struct_a050', 'Balanced Mix (50% Structure)')
    ]

    travelers = ['boulevardier', 'martinez', 'aviation', 'corpse_reviver_2',
                 'vesper', 'division_bell', 'penicillin']

    for idx, (strategy_key, title) in enumerate(strategies):
        ax = axes[idx // 2, idx % 2]
        ax.set_facecolor('#1a1a1d')

        points = data['strategies'][strategy_key]['points']

        # Plot all points in gray
        all_x = [points[name]['x'] for name in points.keys()]
        all_y = [points[name]['y'] for name in points.keys()]
        ax.scatter(all_x, all_y, c='#444444', s=20, alpha=0.3)

        # Highlight travelers
        for traveler in travelers:
            if traveler in points:
                x, y = points[traveler]['x'], points[traveler]['y']
                ax.scatter(x, y, c='#D4AF37', s=100, alpha=0.9, edgecolors='#F5F5DC', linewidth=1)
                display_name = traveler.replace('_', ' ').title()
                ax.annotate(display_name, (x, y), xytext=(5, 5),
                           textcoords='offset points', fontsize=9,
                           color='#D4AF37', weight='bold')

        ax.set_title(title, fontsize=12, color='#D4AF37', weight='bold')
        ax.set_xlabel('UMAP 1', fontsize=10, color='#666666')
        ax.set_ylabel('UMAP 2', fontsize=10, color='#666666')
        ax.grid(False)
        ax.tick_params(colors='#666666')

        for spine in ax.spines.values():
            spine.set_edgecolor('#4a4a3d')

    plt.suptitle('Cocktail Travelers: Drinks that Move Between Neighborhoods',
                 fontsize=16, color='#D4AF37', weight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('viz/travelers_comparison.svg', dpi=150, facecolor='#1a1a1d', edgecolor='none')
    plt.close()

# Create output directory if it doesn't exist
os.makedirs('viz', exist_ok=True)

# Generate visualizations
print("Generating cluster visualizations...")

create_visualization('blend', 'Pure Flavor Profile (BLEND)', 'viz/clusters_blend.svg')
create_visualization('role_slot', 'Recipe Grammar (ROLE-SLOT)', 'viz/clusters_role_slot.svg')
create_visualization('perceptual', 'Intensity-Weighted (PERCEPTUAL)', 'viz/clusters_perceptual.svg')
create_visualization('blend_struct_a050', 'Balanced Mix - 50% Structure', 'viz/clusters_blend_struct_50.svg')

generate_comparison_plot()

print("Visualizations generated successfully!")
print("Files created in viz/ directory:")
print("  - clusters_blend.svg")
print("  - clusters_role_slot.svg")
print("  - clusters_perceptual.svg")
print("  - clusters_blend_struct_50.svg")
print("  - travelers_comparison.svg")