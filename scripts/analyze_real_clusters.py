#!/usr/bin/env python3
"""
Analyze actual clusters in the cocktail data using k-means and other methods.
Find real groupings rather than predetermined ones.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from collections import defaultdict
import os

# Load data
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

def analyze_strategy_clusters(strategy_key, title):
    """Analyze and visualize actual clusters for a given strategy."""

    print(f"\n{'='*60}")
    print(f"Analyzing: {title}")
    print('='*60)

    # Get points for this strategy
    points = data['strategies'][strategy_key]['points']

    # Convert to numpy array
    cocktail_names = list(points.keys())
    X = np.array([[points[name]['x'], points[name]['y']] for name in cocktail_names])

    # Try different numbers of clusters and find optimal
    silhouette_scores = []
    K_range = range(3, 12)

    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        score = silhouette_score(X, labels)
        silhouette_scores.append(score)

    # Find optimal k (highest silhouette score)
    optimal_k = K_range[np.argmax(silhouette_scores)]
    print(f"Optimal number of clusters: {optimal_k} (silhouette score: {max(silhouette_scores):.3f})")

    # Run k-means with optimal k
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    # Group cocktails by cluster
    clusters = defaultdict(list)
    for i, name in enumerate(cocktail_names):
        clusters[labels[i]].append(name)

    # Print cluster contents
    print(f"\nFound {optimal_k} clusters:")
    for cluster_id in sorted(clusters.keys()):
        members = clusters[cluster_id]
        print(f"\nCluster {cluster_id + 1} ({len(members)} members):")

        # Show first 10 members
        sample = members[:10]
        print("  Members:", ', '.join([n.replace('_', ' ').title() for n in sample]))
        if len(members) > 10:
            print(f"  ... and {len(members) - 10} more")

        # Try to identify common characteristics
        if strategy_key == 'blend':
            # Check base spirits
            base_spirits = []
            for name in members[:5]:
                if name in data['recipes']:
                    base = data['recipes'][name].get('base_spirit', 'unknown')
                    base_spirits.append(base)
            if base_spirits:
                print(f"  Common base spirits: {', '.join(set(base_spirits))}")

    # Create visualization
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor('#1a1a1d')
    ax.set_facecolor('#1a1a1d')

    # Color palette for clusters
    colors = ['#50C878', '#CD7F32', '#C0C0C0', '#E0115F', '#0F52BA',
              '#8B4513', '#FFD700', '#4B0082', '#FF69B4', '#00CED1', '#FF4500', '#32CD32']

    # Plot each cluster
    for cluster_id in sorted(clusters.keys()):
        cluster_points = []
        for name in clusters[cluster_id]:
            cluster_points.append([points[name]['x'], points[name]['y']])
        cluster_points = np.array(cluster_points)

        color = colors[cluster_id % len(colors)]

        # Plot points
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1],
                  c=color, s=60, alpha=0.7, edgecolors='#F5F5DC', linewidth=0.5,
                  label=f'Cluster {cluster_id + 1}')

        # Draw convex hull
        if len(cluster_points) >= 3:
            from scipy.spatial import ConvexHull
            try:
                hull = ConvexHull(cluster_points)
                for simplex in hull.simplices:
                    ax.plot(cluster_points[simplex, 0], cluster_points[simplex, 1],
                           color=color, alpha=0.3, linewidth=1.5, linestyle='--')

                # Fill the hull with very low alpha
                from matplotlib.patches import Polygon
                hull_points = cluster_points[hull.vertices]
                poly = Polygon(hull_points, alpha=0.05, facecolor=color)
                ax.add_patch(poly)
            except:
                pass

    # Add labels for notable cocktails
    notable = ['martini', 'manhattan', 'negroni', 'daiquiri', 'old_fashioned',
               'margarita', 'mojito', 'boulevardier', 'last_word', 'aviation',
               'whiskey_sour', 'gimlet', 'aperol_spritz']

    for name in notable:
        if name in points:
            x, y = points[name]['x'], points[name]['y']
            display_name = name.replace('_', ' ').title()

            # Find which cluster this cocktail belongs to
            idx = cocktail_names.index(name)
            cluster_color = colors[labels[idx] % len(colors)]

            ax.annotate(display_name, (x, y),
                       xytext=(3, 3), textcoords='offset points',
                       fontsize=10, color='#F5F5DC', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3',
                                facecolor=cluster_color, alpha=0.3,
                                edgecolor='none'))

    ax.set_title(title, fontsize=16, color='#D4AF37', weight='bold', pad=20)
    ax.set_xlabel('UMAP Dimension 1', fontsize=12, color='#C5C5B0')
    ax.set_ylabel('UMAP Dimension 2', fontsize=12, color='#C5C5B0')
    ax.grid(False)
    ax.tick_params(colors='#666666')

    for spine in ax.spines.values():
        spine.set_edgecolor('#4a4a3d')

    # Add legend
    ax.legend(loc='upper right', framealpha=0.9, facecolor='#2d2d30',
             edgecolor='#4a4a3d', labelcolor='#C5C5B0')

    plt.tight_layout()

    # Save the figure
    output_file = f'viz/kmeans_{strategy_key}.svg'
    plt.savefig(output_file, dpi=150, facecolor='#1a1a1d', edgecolor='none')
    plt.close()

    print(f"\nVisualization saved to {output_file}")

    return clusters, labels, optimal_k

# Analyze each strategy
strategies = [
    ('blend', 'Pure Flavor (BLEND)'),
    ('role_slot', 'Recipe Grammar (ROLE-SLOT)'),
    ('perceptual', 'Intensity-Weighted (PERCEPTUAL)'),
    ('blend_struct_a050', 'Balanced Mix (50% Structure)')
]

all_results = {}
for strategy_key, title in strategies:
    clusters, labels, k = analyze_strategy_clusters(strategy_key, title)
    all_results[strategy_key] = {
        'clusters': dict(clusters),
        'optimal_k': k,
        'title': title
    }

# Save results for use in HTML generation
# Convert numpy types to Python types for JSON serialization
json_results = {}
for strategy_key, result in all_results.items():
    json_results[strategy_key] = {
        'clusters': {str(k): v for k, v in result['clusters'].items()},
        'optimal_k': int(result['optimal_k']),
        'title': result['title']
    }

with open('viz/cluster_analysis.json', 'w') as f:
    json.dump(json_results, f, indent=2)

print("\n" + "="*60)
print("Analysis complete!")
print("Results saved to viz/cluster_analysis.json")
print("Visualizations saved to viz/kmeans_*.svg")