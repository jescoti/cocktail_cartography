#!/usr/bin/env python3
"""
Create improved cluster visualizations with:
1. Intelligent cluster naming based on actual cocktail analysis
2. Force-directed label placement to avoid overlaps
3. Labels that stay within canvas bounds
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.spatial import ConvexHull
from collections import Counter, defaultdict
import os

# Load data
print("Loading cocktail data...")
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

# Create output directory
os.makedirs('viz/improved', exist_ok=True)

def analyze_cocktail_characteristics(members):
    """Analyze a cluster's cocktails to understand their characteristics."""
    characteristics = {
        'base_spirits': Counter(),
        'citrus': 0,
        'bitter': 0,
        'sweet': 0,
        'stirred': 0,
        'shaken': 0,
        'built': 0,
        'has_vermouth': 0,
        'has_liqueur': 0,
        'is_sour': 0,
        'is_old_fashioned': 0,
        'is_highball': 0,
        'has_egg': 0,
        'has_cream': 0,
        'has_wine': 0,
        'tiki': 0
    }

    # Keywords for categorization
    sour_cocktails = ['sour', 'daiquiri', 'margarita', 'gimlet', 'cosmopolitan',
                     'sidecar', 'aviation', 'bee', 'clover', 'pisco', 'caipirinha']

    bitter_cocktails = ['negroni', 'americano', 'boulevardier', 'campari',
                       'aperol', 'cynar', 'fernet', 'paper_plane']

    old_fashioned_variants = ['old_fashioned', 'sazerac', 'oaxaca', 'rum_old',
                              'scotch_old', 'irish_old', 'tequila_old']

    tiki_cocktails = ['mai_tai', 'zombie', 'painkiller', 'jungle_bird',
                     'navy_grog', 'scorpion', 'hurricane']

    highball_cocktails = ['highball', 'collins', 'fizz', 'rickey', 'buck',
                         'mule', 'mojito', 'julep', 'spritz', 'tonic']

    cream_cocktails = ['alexander', 'white_russian', 'mudslide', 'grasshopper',
                      'brandy_milk', 'ramos']

    # Analyze each cocktail
    for cocktail_name in members:
        lower_name = cocktail_name.lower()

        # Check for sours
        if any(s in lower_name for s in sour_cocktails):
            characteristics['is_sour'] += 1
            characteristics['shaken'] += 1
            characteristics['citrus'] += 1

        # Check for bitter/amari
        if any(b in lower_name for b in bitter_cocktails):
            characteristics['bitter'] += 1

        # Check for Old Fashioned variants
        if any(of in lower_name for of in old_fashioned_variants):
            characteristics['is_old_fashioned'] += 1
            characteristics['built'] += 1

        # Check for Tiki
        if any(t in lower_name for t in tiki_cocktails):
            characteristics['tiki'] += 1
            characteristics['shaken'] += 1

        # Check for highballs
        if any(h in lower_name for h in highball_cocktails):
            characteristics['is_highball'] += 1
            characteristics['built'] += 1

        # Check for cream drinks
        if any(c in lower_name for c in cream_cocktails):
            characteristics['has_cream'] += 1
            characteristics['shaken'] += 1

        # Check specific ingredients
        if 'manhattan' in lower_name or 'martini' in lower_name or 'martinez' in lower_name:
            characteristics['stirred'] += 1
            characteristics['has_vermouth'] += 1

        # Base spirit detection
        if 'whiskey' in lower_name or 'bourbon' in lower_name or 'rye' in lower_name:
            characteristics['base_spirits']['whiskey'] += 1
        elif 'gin' in lower_name or 'martini' in lower_name or 'aviation' in lower_name:
            characteristics['base_spirits']['gin'] += 1
        elif 'rum' in lower_name or 'mai_tai' in lower_name or 'daiquiri' in lower_name:
            characteristics['base_spirits']['rum'] += 1
        elif 'tequila' in lower_name or 'margarita' in lower_name or 'paloma' in lower_name:
            characteristics['base_spirits']['tequila'] += 1
        elif 'vodka' in lower_name:
            characteristics['base_spirits']['vodka'] += 1
        elif 'brandy' in lower_name or 'cognac' in lower_name or 'sidecar' in lower_name:
            characteristics['base_spirits']['brandy'] += 1

        # Check for wine-based
        if 'spritz' in lower_name or 'adonis' in lower_name or 'sherry' in lower_name:
            characteristics['has_wine'] += 1

    return characteristics

def generate_intelligent_cluster_name(members, cluster_id):
    """Generate a descriptive name based on actual cluster content."""

    if len(members) == 0:
        return f"Empty Cluster {cluster_id}"

    # Analyze the cluster
    chars = analyze_cocktail_characteristics(members)
    total = len(members)

    # Key cocktails that define categories
    signature_cocktails = {
        'manhattan': 'Manhattan Family',
        'martini': 'Martini Family',
        'old_fashioned': 'Old Fashioned Variations',
        'negroni': 'Negroni & Bitter Cocktails',
        'daiquiri': 'Daiquiri & Rum Sours',
        'margarita': 'Margaritas & Tequila Sours',
        'mai_tai': 'Tiki & Tropical',
        'whiskey_sour': 'Whiskey Sours',
        'aviation': 'Gin Sours & Aviation',
        'sidecar': 'Brandy Sours',
        'mojito': 'Refreshing Highballs',
        'last_word': 'Equal Parts Sours',
        'boulevardier': 'Whiskey & Bitter',
        'aperol_spritz': 'Spritzes & Wine Cocktails',
        'ramos_gin_fizz': 'Fizzes & Foam',
        'french_75': 'Champagne Cocktails',
        'paper_plane': 'Modern Classics'
    }

    # Check for signature cocktails first
    for sig, name in signature_cocktails.items():
        if any(sig in m.lower() for m in members[:5]):  # Check top 5 members
            # Verify it's a good fit
            if 'Manhattan' in name and chars['stirred'] > total * 0.5:
                return name
            elif 'Martini' in name and chars['base_spirits']['gin'] > total * 0.3:
                return name
            elif 'Old Fashioned' in name and chars['is_old_fashioned'] > total * 0.5:
                return name
            elif 'Negroni' in name and chars['bitter'] > total * 0.3:
                return name
            elif 'Sour' in name and chars['is_sour'] > total * 0.5:
                return name
            elif 'Tiki' in name and chars['tiki'] > total * 0.3:
                return name
            elif sig in ['last_word', 'paper_plane', 'boulevardier', 'aviation']:
                return name

    # Generate name based on characteristics

    # Check for Old Fashioned dominance
    if chars['is_old_fashioned'] > total * 0.6:
        return "Old Fashioned Variations"

    # Check for sour dominance
    if chars['is_sour'] > total * 0.6:
        # Sub-categorize sours
        if chars['base_spirits']['whiskey'] > total * 0.4:
            return "Whiskey Sours"
        elif chars['base_spirits']['gin'] > total * 0.4:
            return "Gin Sours"
        elif chars['base_spirits']['rum'] > total * 0.4:
            return "Rum & Tropical Sours"
        elif chars['base_spirits']['tequila'] > total * 0.3:
            return "Tequila & Agave Sours"
        else:
            return "Classic Sours"

    # Check for bitter cocktails
    if chars['bitter'] > total * 0.4:
        return "Bitter & Amaro Cocktails"

    # Check for stirred drinks
    if chars['stirred'] > total * 0.6:
        if chars['has_vermouth'] > total * 0.5:
            return "Stirred & Vermouth"
        else:
            return "Spirit-Forward Stirred"

    # Check for tiki
    if chars['tiki'] > total * 0.3:
        return "Tiki & Tropical"

    # Check for highballs
    if chars['is_highball'] > total * 0.5:
        return "Highballs & Refreshers"

    # Check for cream drinks
    if chars['has_cream'] > total * 0.3:
        return "Cream & Dessert Cocktails"

    # Check for wine-based
    if chars['has_wine'] > total * 0.3:
        return "Wine & Aperitif Cocktails"

    # Base spirit categorization
    dominant_spirit = chars['base_spirits'].most_common(1)
    if dominant_spirit and dominant_spirit[0][1] > total * 0.5:
        spirit = dominant_spirit[0][0].title()
        if chars['shaken'] > chars['stirred']:
            return f"{spirit} Cocktails (Shaken)"
        elif chars['stirred'] > chars['shaken']:
            return f"{spirit} Cocktails (Stirred)"
        else:
            return f"{spirit}-Based Cocktails"

    # Size-based fallback with more detail
    if total > 40:
        return "Large Mixed Category"
    elif total > 20:
        if chars['shaken'] > chars['stirred']:
            return "Mixed Shaken Cocktails"
        elif chars['stirred'] > chars['shaken']:
            return "Mixed Stirred Cocktails"
        else:
            return "Diverse Cocktails"
    elif total > 10:
        return "Medium Cluster"
    elif total > 5:
        return "Small Specialty Group"
    else:
        # For very small clusters, just list the cocktails
        clean_names = [m.replace('_', ' ').title() for m in members[:3]]
        return f"{', '.join(clean_names)}..."

def adjust_label_positions(labels, positions, canvas_bounds, min_distance=0.1):
    """Adjust label positions to avoid overlaps and stay in bounds."""
    adjusted = positions.copy()
    n_labels = len(labels)

    # Canvas boundaries with padding
    x_min, x_max, y_min, y_max = canvas_bounds
    padding = 0.05 * (x_max - x_min)

    # Iterate to resolve conflicts
    for iteration in range(20):  # Max iterations to prevent infinite loop
        moved = False

        for i in range(n_labels):
            if labels[i] is None:
                continue

            x_i, y_i = adjusted[i]

            # Keep in bounds
            if x_i < x_min + padding:
                adjusted[i][0] = x_min + padding
                moved = True
            elif x_i > x_max - padding:
                adjusted[i][0] = x_max - padding
                moved = True

            if y_i < y_min + padding:
                adjusted[i][1] = y_min + padding
                moved = True
            elif y_i > y_max - padding:
                adjusted[i][1] = y_max - padding
                moved = True

            # Check for overlaps with other labels
            for j in range(i + 1, n_labels):
                if labels[j] is None:
                    continue

                x_j, y_j = adjusted[j]
                distance = np.sqrt((x_i - x_j)**2 + (y_i - y_j)**2)

                if distance < min_distance:
                    # Move labels apart
                    dx = x_j - x_i
                    dy = y_j - y_i

                    # Normalize
                    if distance > 0:
                        dx /= distance
                        dy /= distance
                    else:
                        # Random direction if exactly overlapping
                        angle = np.random.random() * 2 * np.pi
                        dx = np.cos(angle)
                        dy = np.sin(angle)

                    # Move each label half the needed distance
                    move_dist = (min_distance - distance) / 2 + 0.01
                    adjusted[i][0] -= dx * move_dist
                    adjusted[i][1] -= dy * move_dist
                    adjusted[j][0] += dx * move_dist
                    adjusted[j][1] += dy * move_dist
                    moved = True

        if not moved:
            break

    return adjusted

def create_improved_visualization(X, labels, cocktail_names, strategy_name, param_str, k):
    """Create an improved visualization with better naming and labels."""

    # Analyze clusters
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        if label >= 0:  # Skip noise points
            clusters[label].append(cocktail_names[i])

    # Generate intelligent cluster names
    cluster_names = {}
    for cluster_id, members in clusters.items():
        cluster_names[cluster_id] = generate_intelligent_cluster_name(members, cluster_id)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 11))
    fig.patch.set_facecolor('#1a1a1d')
    ax.set_facecolor('#1a1a1d')

    # Color palette - colorblind friendly
    colors = ['#2E7D32', '#C62828', '#1565C0', '#F57C00', '#7B1FA2',
              '#00838F', '#5D4037', '#37474F', '#FF6F00', '#4527A0',
              '#D84315', '#00695C']

    # Plot each cluster
    for cluster_id in sorted(clusters.keys()):
        cluster_points = []
        cluster_indices = []
        for i, name in enumerate(cocktail_names):
            if labels[i] == cluster_id:
                cluster_points.append([X[i, 0], X[i, 1]])
                cluster_indices.append(i)

        if len(cluster_points) == 0:
            continue

        cluster_points = np.array(cluster_points)
        color = colors[cluster_id % len(colors)]

        # Plot points
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1],
                  c=[color], s=100, alpha=0.8, edgecolors='white', linewidth=0.8)

        # Draw smooth boundary with padding
        if len(cluster_points) >= 3:
            try:
                # Add padding to hull
                center = np.mean(cluster_points, axis=0)
                padded_points = center + 1.2 * (cluster_points - center)
                hull = ConvexHull(padded_points)

                # Draw hull lines
                for simplex in hull.simplices:
                    ax.plot(padded_points[simplex, 0], padded_points[simplex, 1],
                           color=color, alpha=0.3, linewidth=2)

                # Fill with very low alpha
                hull_points = padded_points[hull.vertices]
                poly = Polygon(hull_points, alpha=0.08, facecolor=color)
                ax.add_patch(poly)
            except:
                pass

        # Add cluster name at center
        if len(cluster_points) > 0:
            center = np.mean(cluster_points, axis=0)
            cluster_name = cluster_names[cluster_id]

            # Adjust font size based on cluster size
            if len(cluster_points) > 20:
                fontsize = 10
            else:
                fontsize = 9

            ax.text(center[0], center[1], cluster_name,
                   fontsize=fontsize, color='white', weight='bold',
                   ha='center', va='center', alpha=0.9,
                   bbox=dict(boxstyle='round,pad=0.4',
                            facecolor='#1a1a1d', alpha=0.8,
                            edgecolor=color, linewidth=1.5))

    # Label selection - prioritize interesting cocktails
    priority_labels = [
        'manhattan', 'martini', 'old_fashioned', 'negroni', 'daiquiri',
        'margarita', 'whiskey_sour', 'boulevardier', 'last_word', 'aviation',
        'penicillin', 'paper_plane', 'mai_tai', 'mojito', 'aperol_spritz',
        'bee_s_knees', 'ramos_gin_fizz', 'sazerac', 'cosmopolitan', 'sidecar'
    ]

    # Additional labels based on cluster edges
    label_targets = []
    label_positions = []
    label_texts = []

    # Get canvas bounds
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    canvas_bounds = (x_min, x_max, y_min, y_max)

    for name in priority_labels:
        if name in cocktail_names:
            idx = cocktail_names.index(name)
            label_targets.append(idx)
            label_positions.append([X[idx, 0], X[idx, 1]])
            label_texts.append(name.replace('_', ' ').title())

    # Adjust label positions to avoid overlap
    if len(label_positions) > 0:
        label_positions = np.array(label_positions)
        adjusted_positions = adjust_label_positions(
            label_texts,
            label_positions.copy(),
            canvas_bounds,
            min_distance=0.08 * (x_max - x_min)  # Scale based on plot size
        )

        # Draw labels with leader lines
        for i, (idx, text) in enumerate(zip(label_targets, label_texts)):
            cluster_color = colors[labels[idx] % len(colors)]

            # Position for label
            label_x, label_y = adjusted_positions[i]

            # Original point position
            point_x, point_y = X[idx, 0], X[idx, 1]

            # Draw leader line if label moved significantly
            distance = np.sqrt((label_x - point_x)**2 + (label_y - point_y)**2)
            if distance > 0.05 * (x_max - x_min):
                ax.plot([point_x, label_x], [point_y, label_y],
                       color='white', alpha=0.3, linewidth=0.5, linestyle=':')

            # Draw label
            ax.annotate(text, (point_x, point_y),
                       xytext=(label_x - point_x, label_y - point_y),
                       textcoords='data',
                       fontsize=8, color='white', alpha=0.95,
                       bbox=dict(boxstyle='round,pad=0.2',
                                facecolor=cluster_color, alpha=0.6,
                                edgecolor='white', linewidth=0.5))

    # Title and labels
    title = f"{strategy_name} - K-Means k={k}"
    ax.set_title(title, fontsize=16, color='#D4AF37', weight='bold', pad=20)
    ax.set_xlabel('Dimension 1', fontsize=11, color='#C5C5B0')
    ax.set_ylabel('Dimension 2', fontsize=11, color='#C5C5B0')
    ax.grid(True, alpha=0.1, color='#4a4a3d', linewidth=0.5)
    ax.tick_params(colors='#666666')

    for spine in ax.spines.values():
        spine.set_edgecolor('#4a4a3d')
        spine.set_linewidth(0.5)

    # Ensure labels stay in frame
    plt.tight_layout()

    # Save
    filename = f'viz/improved/{strategy_name}_{param_str}_kmeans_k{k}.svg'
    plt.savefig(filename, dpi=150, facecolor='#1a1a1d', bbox_inches='tight')
    plt.close()

    return filename, cluster_names

# Key visualizations to regenerate
visualizations_to_create = [
    ('blend_struct_a000', 'alpha_0.00', 'Alpha=0 (Pure Flavor)', 8),
    ('blend_struct_a000', 'alpha_0.00', 'Alpha=0 (Pure Flavor)', 3),
    ('blend_struct_a055', 'alpha_0.55', 'Alpha=0.55 (Sweet Spot)', 3),
    ('blend_struct_a055', 'alpha_0.55', 'Alpha=0.55 (Sweet Spot)', 4),
    ('blend_struct_a070', 'alpha_0.70', 'Alpha=0.70 (Innovation Zone)', 5),
]

print("Creating improved visualizations...")
print("="*60)

for strategy_key, param_str, display_name, k in visualizations_to_create:
    print(f"\nGenerating: {display_name} with k={k}")

    # Get data
    strategy_data = data['strategies'].get(strategy_key, {})
    if 'points' in strategy_data:
        points = strategy_data['points']
    elif 'projects' in strategy_data:
        points = strategy_data['projects']
    else:
        print(f"  No data for {strategy_key}")
        continue

    # Convert to arrays
    cocktail_names = list(points.keys())
    X = np.array([[points[name]['x'], points[name]['y']] for name in cocktail_names])

    # Run k-means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    silhouette = silhouette_score(X, labels)

    # Create visualization
    filename, cluster_names = create_improved_visualization(
        X, labels, cocktail_names, display_name, param_str, k
    )

    print(f"  Created: {filename}")
    print(f"  Silhouette score: {silhouette:.3f}")
    print("  Clusters:")
    for cid, name in sorted(cluster_names.items()):
        print(f"    {cid}: {name}")

print("\n" + "="*60)
print("Improved visualizations complete!")
print("Check viz/improved/ directory for results")