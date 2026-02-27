#!/usr/bin/env python3
"""
Create improved tau visualizations showing the whiskey sour island.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.spatial import ConvexHull
from collections import defaultdict
import os

# Load data
print("Loading tau data...")
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

# Import functions from improved script
import sys
sys.path.append(os.path.dirname(__file__))
from create_improved_visualizations import (
    generate_intelligent_cluster_name,
    adjust_label_positions
)

# Create output directory
os.makedirs('viz/improved', exist_ok=True)

def create_tau_visualization(tau_val, k, highlight_island=False):
    """Create visualization for tau parameter with optional island highlighting."""

    print(f"\nGenerating: Tau={tau_val} with k={k}")

    # Get tau data
    tau_data = data['strategies']['tau'].get(tau_val, {})
    if 'points' not in tau_data and 'projects' not in tau_data:
        print(f"  No point data for tau={tau_val}")
        return None

    # Get points
    if 'points' in tau_data:
        points = tau_data['points']
    else:
        points = tau_data['projects']

    # Convert to arrays
    cocktail_names = list(points.keys())
    X = np.array([[points[name]['x'], points[name]['y']] for name in cocktail_names])

    # Run k-means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    silhouette = silhouette_score(X, labels)

    # Analyze clusters
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        clusters[label].append(cocktail_names[i])

    # Generate cluster names
    cluster_names = {}
    whiskey_sour_cluster = None
    for cluster_id, members in clusters.items():
        name = generate_intelligent_cluster_name(members, cluster_id)
        cluster_names[cluster_id] = name

        # Check if this is the whiskey sour island
        if 'whiskey_sour' in members and len(members) <= 6:
            whiskey_sour_cluster = cluster_id
            cluster_names[cluster_id] = "🏝️ Whiskey Sour Island"
            print(f"  Found Whiskey Sour Island: {members}")

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 11))
    fig.patch.set_facecolor('#1a1a1d')
    ax.set_facecolor('#1a1a1d')

    # Color palette
    colors = ['#2E7D32', '#C62828', '#1565C0', '#F57C00', '#7B1FA2',
              '#00838F', '#5D4037', '#37474F', '#FF6F00', '#4527A0']

    # Plot each cluster
    for cluster_id in sorted(clusters.keys()):
        cluster_points = []
        for i, name in enumerate(cocktail_names):
            if labels[i] == cluster_id:
                cluster_points.append([X[i, 0], X[i, 1]])

        if len(cluster_points) == 0:
            continue

        cluster_points = np.array(cluster_points)

        # Special styling for whiskey sour island
        if cluster_id == whiskey_sour_cluster:
            color = '#FFD700'  # Gold for the island
            alpha = 0.9
            edge_style = '--'
            edge_width = 3
        else:
            color = colors[cluster_id % len(colors)]
            alpha = 0.8
            edge_style = '-'
            edge_width = 2

        # Plot points
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1],
                  c=[color], s=120 if cluster_id == whiskey_sour_cluster else 100,
                  alpha=alpha, edgecolors='white', linewidth=1.0)

        # Draw boundary
        if len(cluster_points) >= 3:
            try:
                center = np.mean(cluster_points, axis=0)
                padded_points = center + 1.25 * (cluster_points - center)
                hull = ConvexHull(padded_points)

                for simplex in hull.simplices:
                    ax.plot(padded_points[simplex, 0], padded_points[simplex, 1],
                           color=color, alpha=0.4, linewidth=edge_width,
                           linestyle=edge_style)

                hull_points = padded_points[hull.vertices]
                poly = Polygon(hull_points, alpha=0.1, facecolor=color)
                ax.add_patch(poly)

                # Add water effect around island
                if cluster_id == whiskey_sour_cluster:
                    for i in range(3):
                        scale = 1.3 + i * 0.1
                        water_points = center + scale * (cluster_points - center)
                        try:
                            water_hull = ConvexHull(water_points)
                            water_hull_points = water_points[water_hull.vertices]
                            water_poly = Polygon(water_hull_points, alpha=0.02,
                                               facecolor='#4A90E2', edgecolor='#4A90E2',
                                               linewidth=1, linestyle=':')
                            ax.add_patch(water_poly)
                        except:
                            pass
            except:
                pass

        # Add cluster name
        if len(cluster_points) > 0:
            center = np.mean(cluster_points, axis=0)
            cluster_name = cluster_names[cluster_id]

            # Special styling for island
            if cluster_id == whiskey_sour_cluster:
                ax.text(center[0], center[1], cluster_name,
                       fontsize=11, color='#FFD700', weight='bold',
                       ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.5',
                                facecolor='#1a1a1d', alpha=0.9,
                                edgecolor='#FFD700', linewidth=2))
            else:
                ax.text(center[0], center[1], cluster_name,
                       fontsize=10, color='white', weight='bold',
                       ha='center', va='center', alpha=0.9,
                       bbox=dict(boxstyle='round,pad=0.4',
                                facecolor='#1a1a1d', alpha=0.8,
                                edgecolor=color, linewidth=1.5))

    # Label key cocktails
    if tau_val == '4.019' and whiskey_sour_cluster is not None:
        # For the island visualization, label all island members
        island_members = clusters[whiskey_sour_cluster]
        label_targets = []
        label_positions = []
        label_texts = []

        for name in island_members:
            if name in cocktail_names:
                idx = cocktail_names.index(name)
                label_targets.append(idx)
                label_positions.append([X[idx, 0], X[idx, 1]])
                label_texts.append(name.replace('_', ' ').title())

        # Also add some non-island cocktails for comparison
        other_cocktails = ['manhattan', 'daiquiri', 'margarita', 'negroni', 'martini']
        for name in other_cocktails:
            if name in cocktail_names and name not in island_members:
                idx = cocktail_names.index(name)
                label_targets.append(idx)
                label_positions.append([X[idx, 0], X[idx, 1]])
                label_texts.append(name.replace('_', ' ').title())
    else:
        # Standard labeling
        priority_labels = [
            'manhattan', 'martini', 'old_fashioned', 'negroni', 'daiquiri',
            'margarita', 'whiskey_sour', 'boulevardier', 'last_word', 'aviation',
            'penicillin', 'paper_plane', 'gold_rush', 'mai_tai', 'mojito'
        ]
        label_targets = []
        label_positions = []
        label_texts = []

        for name in priority_labels:
            if name in cocktail_names:
                idx = cocktail_names.index(name)
                label_targets.append(idx)
                label_positions.append([X[idx, 0], X[idx, 1]])
                label_texts.append(name.replace('_', ' ').title())

    # Adjust and draw labels
    if len(label_positions) > 0:
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        canvas_bounds = (x_min, x_max, y_min, y_max)

        label_positions = np.array(label_positions)
        adjusted_positions = adjust_label_positions(
            label_texts,
            label_positions.copy(),
            canvas_bounds,
            min_distance=0.08 * (x_max - x_min)
        )

        for i, (idx, text) in enumerate(zip(label_targets, label_texts)):
            # Special styling for island members
            if cocktail_names[idx] in clusters.get(whiskey_sour_cluster, []):
                bg_color = '#FFD700'
                text_color = '#1a1a1d'
                alpha = 0.9
            else:
                cluster_color = colors[labels[idx] % len(colors)]
                bg_color = cluster_color
                text_color = 'white'
                alpha = 0.6

            label_x, label_y = adjusted_positions[i]
            point_x, point_y = X[idx, 0], X[idx, 1]

            # Draw leader line if needed
            distance = np.sqrt((label_x - point_x)**2 + (label_y - point_y)**2)
            if distance > 0.05 * (x_max - x_min):
                ax.plot([point_x, label_x], [point_y, label_y],
                       color='white', alpha=0.3, linewidth=0.5, linestyle=':')

            ax.annotate(text, (point_x, point_y),
                       xytext=(label_x - point_x, label_y - point_y),
                       textcoords='data',
                       fontsize=9, color=text_color, alpha=0.95,
                       bbox=dict(boxstyle='round,pad=0.2',
                                facecolor=bg_color, alpha=alpha,
                                edgecolor='white', linewidth=0.5))

    # Title and labels
    tau_interpretation = {
        '0.14': 'Very Low (Intensity Dominates)',
        '0.383': 'Low (Punchy Accents)',
        '0.75': 'Medium (Balanced)',
        '4.019': 'Transition (Island Emerges)',
        '15.399': 'High (Volume Emerging)',
        '115.478': 'Very High (Volume Dominates)'
    }

    tau_desc = tau_interpretation.get(tau_val, '')
    title = f"Tau={tau_val} {tau_desc} - K-Means k={k}"
    ax.set_title(title, fontsize=16, color='#D4AF37', weight='bold', pad=20)

    # Add subtitle if island present
    if whiskey_sour_cluster is not None:
        ax.text(0.5, 0.95, f"🏝️ Whiskey Sour Island Population: {len(clusters[whiskey_sour_cluster])} cocktails",
               transform=ax.transAxes, fontsize=11, color='#FFD700',
               ha='center', va='top', weight='bold')

    ax.set_xlabel('Dimension 1', fontsize=11, color='#C5C5B0')
    ax.set_ylabel('Dimension 2', fontsize=11, color='#C5C5B0')
    ax.grid(True, alpha=0.1, color='#4a4a3d', linewidth=0.5)
    ax.tick_params(colors='#666666')

    for spine in ax.spines.values():
        spine.set_edgecolor('#4a4a3d')
        spine.set_linewidth(0.5)

    plt.tight_layout()

    # Save
    filename = f'viz/improved/tau_{tau_val}_k{k}.svg'
    plt.savefig(filename, dpi=150, facecolor='#1a1a1d', bbox_inches='tight')
    plt.close()

    print(f"  Created: {filename}")
    print(f"  Silhouette: {silhouette:.3f}")

    return filename

# Create key tau visualizations
print("Creating tau visualizations...")
print("="*60)

tau_visualizations = [
    ('0.383', 3),  # Your 3 clear groups
    ('0.75', 4),   # Your 4 very clear clusters
    ('4.019', 5),  # Whiskey sour island emerges
    ('4.019', 9),  # Show island more clearly with higher k
    ('15.399', 4), # Island persists
]

for tau_val, k in tau_visualizations:
    create_tau_visualization(tau_val, k, highlight_island=(tau_val == '4.019'))

print("\n" + "="*60)
print("Tau visualizations complete!")