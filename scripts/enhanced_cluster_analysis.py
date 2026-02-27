#!/usr/bin/env python3
"""
Enhanced clustering analysis with multiple strategies and subcluster detection.
Improvements:
- Analyzes 8+ vectorization strategies
- Finds subclusters within large groups
- Uses smoother boundaries (splines instead of convex hulls)
- Better label placement
- Documents traveler cocktails
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from collections import defaultdict
import os
from scipy.interpolate import splprep, splev
from scipy.spatial import ConvexHull

# Load data
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

def get_smooth_boundary(points, smoothing=0.1):
    """Create smooth boundary around points using splines."""
    if len(points) < 3:
        return points

    try:
        # Get convex hull as starting boundary
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]

        # Close the loop
        hull_points = np.vstack([hull_points, hull_points[0]])

        # Fit spline
        tck, u = splprep([hull_points[:, 0], hull_points[:, 1]],
                        s=smoothing * len(hull_points), per=True)

        # Evaluate spline at many points for smooth curve
        u_new = np.linspace(0, 1, 100)
        smooth_boundary = splev(u_new, tck)

        return np.column_stack(smooth_boundary)
    except:
        # Fallback to convex hull if spline fails
        return hull_points

def find_subclusters(X, cocktail_names, parent_cluster_indices, max_k=6):
    """Find subclusters within a larger cluster."""
    if len(parent_cluster_indices) < max_k:
        return None

    # Get points for this cluster
    cluster_X = X[parent_cluster_indices]
    cluster_names = [cocktail_names[i] for i in parent_cluster_indices]

    # Try different k values
    best_k = 2
    best_score = -1

    for k in range(2, min(max_k + 1, len(cluster_X))):
        if k >= len(cluster_X):
            break
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(cluster_X)

        if len(set(labels)) > 1:  # Ensure we actually got multiple clusters
            score = silhouette_score(cluster_X, labels)
            if score > best_score:
                best_score = score
                best_k = k

    # Run with best k
    if best_k > 1:
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(cluster_X)

        # Group by subcluster
        subclusters = defaultdict(list)
        for i, name in enumerate(cluster_names):
            subclusters[labels[i]].append(name)

        return subclusters, best_k, best_score

    return None

def get_cluster_name(members, data):
    """Generate a descriptive name for a cluster based on its members."""
    # Count common characteristics
    base_spirits = defaultdict(int)
    styles = defaultdict(int)

    for name in members[:min(10, len(members))]:  # Sample first 10
        if name in data.get('recipes', {}):
            recipe = data['recipes'][name]
            if 'base_spirit' in recipe:
                base_spirits[recipe['base_spirit']] += 1
            if 'style' in recipe:
                styles[recipe['style']] += 1

    # Look for notable cocktails that define the cluster
    classic_markers = {
        'martini': 'Martini Territory',
        'manhattan': 'Manhattan Family',
        'old_fashioned': 'Old Fashioned Realm',
        'margarita': 'Margarita Zone',
        'daiquiri': 'Daiquiri Classics',
        'negroni': 'Negroni Variations',
        'mojito': 'Refreshing Highballs',
        'whiskey_sour': 'Whiskey Sours',
        'mai_tai': 'Tiki Paradise',
        'last_word': 'Herbal Complexity'
    }

    for marker, cluster_name in classic_markers.items():
        if marker in members[:5]:  # If marker is in top 5 members
            return cluster_name

    # Fall back to base spirit if dominant
    if base_spirits:
        dominant_spirit = max(base_spirits, key=base_spirits.get)
        if base_spirits[dominant_spirit] >= len(members) * 0.5:
            return f"{dominant_spirit.title()} Cocktails"

    # Generic name based on size
    if len(members) > 30:
        return "Large Citrus Family"
    elif len(members) > 15:
        return "Mixed Classics"
    else:
        return "Specialty Drinks"

def analyze_strategy_clusters(strategy_key, title, force_k=None, find_subs=True):
    """
    Analyze and visualize actual clusters for a given strategy.

    Args:
        strategy_key: The strategy to analyze
        title: Display title
        force_k: If set, use this k value instead of finding optimal
        find_subs: Whether to find subclusters in large groups
    """

    print(f"\n{'='*60}")
    print(f"Analyzing: {title}")
    print('='*60)

    # Check if strategy exists
    if strategy_key not in data['strategies']:
        print(f"Warning: Strategy '{strategy_key}' not found in data. Skipping.")
        return {}, [], 0, {}

    # Get points for this strategy - check for 'points' or 'projects' key
    strategy_data = data['strategies'][strategy_key]
    if 'points' in strategy_data:
        points = strategy_data['points']
    elif 'projects' in strategy_data:
        points = strategy_data['projects']
    else:
        print(f"Warning: No points/projects data for strategy '{strategy_key}'. Skipping.")
        return {}, [], 0, {}

    # Convert to numpy array
    cocktail_names = list(points.keys())
    X = np.array([[points[name]['x'], points[name]['y']] for name in cocktail_names])

    if force_k:
        optimal_k = force_k
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        score = silhouette_score(X, labels)
        print(f"Using k={optimal_k} (silhouette score: {score:.3f})")
    else:
        # Try different numbers of clusters
        silhouette_scores = []
        K_range = range(3, min(12, len(X) // 3))

        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            score = silhouette_score(X, labels)
            silhouette_scores.append(score)

        # Find optimal k
        optimal_k = K_range[np.argmax(silhouette_scores)]
        print(f"Optimal number of clusters: {optimal_k} (silhouette score: {max(silhouette_scores):.3f})")

        # Run k-means with optimal k
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

    # Group cocktails by cluster
    clusters = defaultdict(list)
    cluster_indices = defaultdict(list)
    for i, name in enumerate(cocktail_names):
        clusters[labels[i]].append(name)
        cluster_indices[labels[i]].append(i)

    # Analyze subclusters for large groups
    subclusters_info = {}

    print(f"\nFound {optimal_k} clusters:")
    for cluster_id in sorted(clusters.keys()):
        members = clusters[cluster_id]
        cluster_name = get_cluster_name(members, data)

        print(f"\nCluster {cluster_id + 1}: {cluster_name} ({len(members)} members)")

        # Show first 8 members
        sample = members[:8]
        print("  Key members:", ', '.join([n.replace('_', ' ').title() for n in sample]))
        if len(members) > 8:
            print(f"  ... and {len(members) - 8} more")

        # Find subclusters if this is a large group
        if find_subs and len(members) >= 15:
            sub_result = find_subclusters(X, cocktail_names, cluster_indices[cluster_id])
            if sub_result:
                subclusters, sub_k, sub_score = sub_result
                subclusters_info[cluster_id] = {
                    'subclusters': subclusters,
                    'k': sub_k,
                    'score': sub_score
                }
                print(f"  → Found {sub_k} subclusters (score: {sub_score:.3f}):")
                for sub_id, sub_members in subclusters.items():
                    print(f"     Subcluster {sub_id + 1}: {', '.join(sub_members[:3])}...")

    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 11))
    fig.patch.set_facecolor('#1a1a1d')
    ax.set_facecolor('#1a1a1d')

    # Color palette - colorblind-friendly
    colors = ['#2E7D32', '#C62828', '#1565C0', '#F57C00', '#7B1FA2',
              '#00838F', '#5D4037', '#37474F', '#FF6F00', '#4527A0']

    # Plot each cluster
    for cluster_id in sorted(clusters.keys()):
        cluster_points = []
        for name in clusters[cluster_id]:
            cluster_points.append([points[name]['x'], points[name]['y']])
        cluster_points = np.array(cluster_points)

        color = colors[cluster_id % len(colors)]
        cluster_name = get_cluster_name(clusters[cluster_id], data)

        # Plot points
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1],
                  c=color, s=80, alpha=0.8, edgecolors='white', linewidth=0.8,
                  label=cluster_name)

        # Draw smooth boundary
        if len(cluster_points) >= 3:
            smooth_boundary = get_smooth_boundary(cluster_points)
            ax.plot(smooth_boundary[:, 0], smooth_boundary[:, 1],
                   color=color, alpha=0.4, linewidth=2.5, linestyle='-')

            # Fill with very low alpha
            from matplotlib.patches import Polygon
            poly = Polygon(smooth_boundary, alpha=0.08, facecolor=color)
            ax.add_patch(poly)

        # Add cluster name on the plot
        center_x = np.mean(cluster_points[:, 0])
        center_y = np.mean(cluster_points[:, 1])
        ax.text(center_x, center_y, cluster_name,
               fontsize=11, color=color, weight='bold',
               ha='center', va='center', alpha=0.7,
               bbox=dict(boxstyle='round,pad=0.4',
                        facecolor='#1a1a1d', alpha=0.7,
                        edgecolor=color, linewidth=1))

    # Enhanced labeling - label more cocktails without overlap
    # Priority cocktails to label
    priority_labels = [
        'martini', 'manhattan', 'negroni', 'daiquiri', 'old_fashioned',
        'margarita', 'mojito', 'boulevardier', 'last_word', 'aviation',
        'whiskey_sour', 'gimlet', 'aperol_spritz', 'mai_tai', 'penicillin',
        'paper_plane', 'bee_s_knees', 'cosmopolitan', 'french_75', 'sazerac'
    ]

    # Track labeled positions to avoid overlap
    labeled_positions = []
    min_distance = 0.15  # Minimum distance between labels

    for name in priority_labels:
        if name in points:
            x, y = points[name]['x'], points[name]['y']

            # Check if too close to existing label
            too_close = False
            for lx, ly in labeled_positions:
                if np.sqrt((x - lx)**2 + (y - ly)**2) < min_distance:
                    too_close = True
                    break

            if not too_close:
                display_name = name.replace('_', ' ').title()

                # Find which cluster this cocktail belongs to
                idx = cocktail_names.index(name)
                cluster_color = colors[labels[idx] % len(colors)]

                ax.annotate(display_name, (x, y),
                           xytext=(4, 4), textcoords='offset points',
                           fontsize=9, color='white', fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.2',
                                    facecolor=cluster_color, alpha=0.5,
                                    edgecolor='white', linewidth=0.5))

                labeled_positions.append((x, y))

    ax.set_title(title, fontsize=18, color='#D4AF37', weight='bold', pad=20)
    ax.set_xlabel('UMAP Dimension 1', fontsize=12, color='#C5C5B0')
    ax.set_ylabel('UMAP Dimension 2', fontsize=12, color='#C5C5B0')
    ax.grid(True, alpha=0.1, color='#4a4a3d')
    ax.tick_params(colors='#666666')

    for spine in ax.spines.values():
        spine.set_edgecolor('#4a4a3d')
        spine.set_linewidth(0.5)

    # Smaller, cleaner legend
    ax.legend(loc='upper right', framealpha=0.9, facecolor='#2d2d30',
             edgecolor='#4a4a3d', labelcolor='#C5C5B0', fontsize=10,
             borderpad=0.5, columnspacing=1, handletextpad=0.5)

    plt.tight_layout()

    # Save the figure
    output_file = f'viz/enhanced_{strategy_key}.svg'
    plt.savefig(output_file, dpi=150, facecolor='#1a1a1d', edgecolor='none')
    plt.close()

    print(f"\nVisualization saved to {output_file}")

    return clusters, labels, optimal_k, subclusters_info

# Analyze more strategies (8+)
strategies = [
    ('blend', 'Pure Flavor (BLEND)'),
    ('role_slot', 'Recipe Grammar (ROLE-SLOT)'),
    ('perceptual', 'Intensity-Weighted (PERCEPTUAL)'),
    ('blend_struct_a025', '25% Structure + 75% Flavor'),
    ('blend_struct_a050', 'Balanced Mix (50/50)'),
    ('blend_struct_a075', '75% Structure + 25% Flavor'),
    ('blend_struct_a100', 'Pure Structure'),
    ('blend_struct_a000', 'Pure Flavor (Alternative)'),
]

# Also analyze BLEND with higher k to find subclusters
print("\n" + "="*60)
print("SPECIAL ANALYSIS: Finding subclusters in large groups")
print("="*60)

all_results = {}

# Regular analysis
for strategy_key, title in strategies:
    clusters, labels, k, subclusters = analyze_strategy_clusters(strategy_key, title)
    all_results[strategy_key] = {
        'clusters': dict(clusters),
        'optimal_k': k,
        'title': title,
        'subclusters': subclusters
    }

# Force higher k for blend to find subclusters
print("\n" + "="*60)
print("Testing BLEND with k=5 and k=6 for subclusters")
analyze_strategy_clusters('blend', 'Pure Flavor (BLEND) - k=5', force_k=5)
analyze_strategy_clusters('blend', 'Pure Flavor (BLEND) - k=6', force_k=6)

# Analyze travelers - cocktails that move between clusters
print("\n" + "="*60)
print("TRAVELER ANALYSIS: Cocktails that move between clusters")
print("="*60)

# Track where each cocktail clusters across strategies
cocktail_clusters = defaultdict(dict)

for strategy_key, result in all_results.items():
    for cluster_id, members in result['clusters'].items():
        for cocktail in members:
            cocktail_clusters[cocktail][strategy_key] = cluster_id

# Find travelers (cocktails that change clusters)
travelers = {}
stable = {}

for cocktail, strategy_clusters in cocktail_clusters.items():
    cluster_values = list(strategy_clusters.values())
    if len(set(cluster_values)) > 1:  # Changes clusters
        travelers[cocktail] = strategy_clusters
    else:
        stable[cocktail] = cluster_values[0]

# Report interesting travelers
notable_travelers = ['boulevardier', 'penicillin', 'last_word', 'paper_plane',
                     'bee_s_knees', 'aperol_spritz', 'mai_tai']

print("\nNotable Travelers:")
for cocktail in notable_travelers:
    if cocktail in travelers:
        print(f"\n{cocktail.replace('_', ' ').title()}:")
        for strategy_key, cluster_id in travelers[cocktail].items():
            if strategy_key in all_results:
                title = all_results[strategy_key]['title']
                # Find cluster companions
                companions = [c for c in all_results[strategy_key]['clusters'][cluster_id]
                            if c != cocktail][:3]
                print(f"  {title}: Cluster {cluster_id + 1} (with {', '.join(companions[:2])}...)")

# Save enhanced results
json_results = {}
for strategy_key, result in all_results.items():
    json_results[strategy_key] = {
        'clusters': {str(k): v for k, v in result['clusters'].items()},
        'optimal_k': int(result['optimal_k']),
        'title': result['title'],
        'subclusters': {str(k): {str(sk): sv for sk, sv in v['subclusters'].items()}
                       for k, v in result.get('subclusters', {}).items()} if result.get('subclusters') else {}
    }

# Add traveler analysis
json_results['travelers'] = {
    'notable': {k: {sk: int(sv) for sk, sv in v.items()}
               for k, v in travelers.items() if k in notable_travelers},
    'total_travelers': len(travelers),
    'total_stable': len(stable)
}

with open('viz/enhanced_cluster_analysis.json', 'w') as f:
    json.dump(json_results, f, indent=2)

print("\n" + "="*60)
print("Enhanced analysis complete!")
print(f"Found {len(travelers)} traveler cocktails and {len(stable)} stable cocktails")
print("Results saved to viz/enhanced_cluster_analysis.json")
print("Visualizations saved to viz/enhanced_*.svg")
print("="*60)