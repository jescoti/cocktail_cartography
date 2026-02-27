#!/usr/bin/env python3
"""
Comprehensive clustering analysis using multiple algorithms.
Generates extensive visualizations and analytical documentation.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, MeanShift, DBSCAN, SpectralClustering, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial import ConvexHull
import umap
from collections import defaultdict, Counter
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Global data variable (will be loaded when needed)
data = None

def load_data():
    """Load the embeddings data if not already loaded."""
    global data
    if data is None:
        print("Loading cocktail data...")
        with open('data/embeddings.json', 'r') as f:
            data = json.load(f)
    return data

def get_cocktail_points(strategy_key, param=None):
    """Get 2D points for a given strategy and optional parameter."""
    data = load_data()
    if param is not None:
        # For tau or other parameterized strategies
        if strategy_key == 'tau' and param in data['strategies']['tau']:
            # Need to project tau embeddings first
            tau_data = data['strategies']['tau'][param]
            if 'embedding' in tau_data:
                # Get embeddings for all cocktails
                embedding_data = tau_data['embedding']
                cocktail_names = list(embedding_data.keys())
                embeddings = np.array([embedding_data[name] for name in cocktail_names])

                # Run UMAP projection
                reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
                points_2d = reducer.fit_transform(embeddings)

                return cocktail_names, points_2d
            else:
                return None, None
        else:
            # For blend_struct with alpha parameter
            strategy_data = data['strategies'].get(strategy_key)
            if strategy_data and ('points' in strategy_data or 'projects' in strategy_data):
                points_data = strategy_data.get('points', strategy_data.get('projects', {}))
                cocktail_names = list(points_data.keys())
                points_2d = np.array([[points_data[name]['x'], points_data[name]['y']]
                                     for name in cocktail_names])
                return cocktail_names, points_2d
    else:
        # Regular strategy without parameters
        strategy_data = data['strategies'].get(strategy_key)
        if strategy_data and ('points' in strategy_data or 'projects' in strategy_data):
            points_data = strategy_data.get('points', strategy_data.get('projects', {}))
            cocktail_names = list(points_data.keys())
            points_2d = np.array([[points_data[name]['x'], points_data[name]['y']]
                                 for name in cocktail_names])
            return cocktail_names, points_2d

    return None, None

def analyze_clusters(labels, cocktail_names, algorithm_name):
    """Analyze cluster composition and characteristics."""
    data = load_data()
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        if label >= 0:  # Skip noise points in DBSCAN
            clusters[label].append(cocktail_names[i])

    analysis = {
        'n_clusters': len(clusters),
        'clusters': {}
    }

    for cluster_id, members in clusters.items():
        # Analyze common characteristics
        base_spirits = []
        for name in members[:10]:  # Sample first 10
            if name in data.get('recipes', {}):
                recipe = data['recipes'][name]
                if 'base_spirit' in recipe:
                    base_spirits.append(recipe['base_spirit'])

        spirit_counts = Counter(base_spirits)
        dominant_spirit = spirit_counts.most_common(1)[0][0] if spirit_counts else 'mixed'

        # Generate cluster name based on content
        cluster_name = generate_cluster_name(members, dominant_spirit)

        analysis['clusters'][cluster_id] = {
            'size': len(members),
            'name': cluster_name,
            'dominant_spirit': dominant_spirit,
            'sample_members': members[:8],
            'all_members': members
        }

    # Find outliers for DBSCAN
    if algorithm_name == 'DBSCAN':
        outliers = [cocktail_names[i] for i, label in enumerate(labels) if label == -1]
        analysis['outliers'] = outliers
        analysis['n_outliers'] = len(outliers)

    return analysis

def generate_cluster_name(members, dominant_spirit):
    """Generate a descriptive name for a cluster based on its members."""
    # Look for signature cocktails
    signatures = {
        'martini': 'Martini Family',
        'manhattan': 'Manhattan Territory',
        'old_fashioned': 'Old Fashioned Realm',
        'negroni': 'Negroni Variations',
        'daiquiri': 'Daiquiri & Sours',
        'margarita': 'Margarita & Citrus',
        'whiskey_sour': 'Whiskey Sours',
        'mojito': 'Refreshing Highballs',
        'last_word': 'Chartreuse Complex',
        'aviation': 'Floral Sophisticates'
    }

    for sig, name in signatures.items():
        if sig in members[:5]:
            return name

    # Fall back to spirit-based naming
    if dominant_spirit and dominant_spirit != 'mixed':
        return f"{dominant_spirit.title()}-Based Cocktails"

    # Size-based fallback
    if len(members) > 30:
        return "Large Mixed Group"
    elif len(members) > 15:
        return "Medium Cluster"
    else:
        return "Small Specialty Group"

def create_visualization(X, labels, cocktail_names, title, filename, analysis):
    """Create a visualization of clustering results."""
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor('#1a1a1d')
    ax.set_facecolor('#1a1a1d')

    # Color palette
    colors = plt.cm.tab20(np.linspace(0, 1, 20))

    # Plot each cluster
    unique_labels = sorted(set(labels))
    for label in unique_labels:
        if label == -1:  # DBSCAN outliers
            mask = labels == label
            ax.scatter(X[mask, 0], X[mask, 1], c='red', s=100, marker='x',
                      label='Outliers', alpha=0.8, edgecolors='white', linewidth=1)
        else:
            mask = labels == label
            cluster_points = X[mask]
            color = colors[label % len(colors)]

            # Plot points
            ax.scatter(cluster_points[:, 0], cluster_points[:, 1],
                      c=[color], s=80, alpha=0.7, edgecolors='white', linewidth=0.5)

            # Draw convex hull with padding
            if len(cluster_points) >= 3:
                try:
                    # Add padding to hull
                    center = np.mean(cluster_points, axis=0)
                    padded_points = center + 1.15 * (cluster_points - center)
                    hull = ConvexHull(padded_points)

                    for simplex in hull.simplices:
                        ax.plot(padded_points[simplex, 0], padded_points[simplex, 1],
                               color=color, alpha=0.3, linewidth=2)

                    # Fill hull with very low alpha
                    hull_points = padded_points[hull.vertices]
                    from matplotlib.patches import Polygon
                    poly = Polygon(hull_points, alpha=0.05, facecolor=color)
                    ax.add_patch(poly)
                except:
                    pass

            # Add cluster label at center
            if label in analysis['clusters']:
                cluster_info = analysis['clusters'][label]
                center = np.mean(cluster_points, axis=0)
                ax.text(center[0], center[1], cluster_info['name'],
                       fontsize=10, color=color, weight='bold',
                       ha='center', va='center', alpha=0.8,
                       bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='#1a1a1d', alpha=0.7,
                                edgecolor=color, linewidth=1))

    # Add labels for notable cocktails
    notable = ['martini', 'manhattan', 'old_fashioned', 'negroni', 'daiquiri',
               'margarita', 'whiskey_sour', 'boulevardier', 'last_word', 'aviation',
               'penicillin', 'paper_plane', 'mai_tai', 'mojito', 'aperol_spritz']

    for i, name in enumerate(cocktail_names):
        if name in notable:
            ax.annotate(name.replace('_', ' ').title(),
                       (X[i, 0], X[i, 1]),
                       xytext=(3, 3), textcoords='offset points',
                       fontsize=8, color='white', alpha=0.8)

    ax.set_title(title, fontsize=14, color='#D4AF37', weight='bold', pad=20)
    ax.set_xlabel('Dimension 1', fontsize=11, color='#C5C5B0')
    ax.set_ylabel('Dimension 2', fontsize=11, color='#C5C5B0')
    ax.grid(True, alpha=0.1, color='#4a4a3d')
    ax.tick_params(colors='#666666')

    for spine in ax.spines.values():
        spine.set_edgecolor('#4a4a3d')
        spine.set_linewidth(0.5)

    plt.tight_layout()
    plt.savefig(filename, dpi=120, facecolor='#1a1a1d', bbox_inches='tight')
    plt.close()

def run_kmeans_analysis(X, cocktail_names, k_range, strategy_name, param_str):
    """Run k-means for different k values and document results."""
    results = {}

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        # Calculate metrics
        silhouette = silhouette_score(X, labels) if k > 1 else 0
        inertia = kmeans.inertia_

        # Analyze clusters
        analysis = analyze_clusters(labels, cocktail_names, 'KMeans')
        analysis['silhouette'] = silhouette
        analysis['inertia'] = inertia

        # Create visualization
        title = f"{strategy_name} - KMeans k={k} (silhouette: {silhouette:.3f})"
        filename = f"viz/clustering_exploration/{strategy_name}_{param_str}_kmeans_k{k}.svg"
        create_visualization(X, labels, cocktail_names, title, filename, analysis)

        results[k] = {
            'labels': labels.tolist(),
            'analysis': analysis,
            'filename': filename
        }

        print(f"  K-Means k={k}: {analysis['n_clusters']} clusters, silhouette={silhouette:.3f}")

    return results

def run_meanshift_analysis(X, cocktail_names, strategy_name, param_str):
    """Run Mean Shift clustering."""
    from sklearn.cluster import estimate_bandwidth

    # Estimate bandwidth
    bandwidth = estimate_bandwidth(X, quantile=0.2, n_samples=len(X))

    ms = MeanShift(bandwidth=bandwidth)
    labels = ms.fit_predict(X)

    analysis = analyze_clusters(labels, cocktail_names, 'MeanShift')
    n_clusters = len(set(labels))

    title = f"{strategy_name} - MeanShift (found {n_clusters} clusters)"
    filename = f"viz/clustering_exploration/{strategy_name}_{param_str}_meanshift.svg"
    create_visualization(X, labels, cocktail_names, title, filename, analysis)

    print(f"  Mean Shift: Found {n_clusters} clusters naturally")

    return {
        'labels': labels.tolist(),
        'analysis': analysis,
        'bandwidth': bandwidth,
        'filename': filename
    }

def run_dbscan_analysis(X, cocktail_names, strategy_name, param_str):
    """Run DBSCAN clustering."""
    # Standardize features
    X_scaled = StandardScaler().fit_transform(X)

    # Try different epsilon values
    results = {}
    eps_values = [0.3, 0.5, 0.7, 1.0]

    for eps in eps_values:
        dbscan = DBSCAN(eps=eps, min_samples=3)
        labels = dbscan.fit_predict(X_scaled)

        analysis = analyze_clusters(labels, cocktail_names, 'DBSCAN')
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_outliers = list(labels).count(-1)

        title = f"{strategy_name} - DBSCAN eps={eps} ({n_clusters} clusters, {n_outliers} outliers)"
        filename = f"viz/clustering_exploration/{strategy_name}_{param_str}_dbscan_eps{eps}.svg"
        create_visualization(X, labels, cocktail_names, title, filename, analysis)

        results[eps] = {
            'labels': labels.tolist(),
            'analysis': analysis,
            'filename': filename
        }

        print(f"  DBSCAN eps={eps}: {n_clusters} clusters, {n_outliers} outliers")

    return results

def run_hierarchical_analysis(X, cocktail_names, strategy_name, param_str):
    """Run hierarchical clustering with different linkage methods."""
    results = {}
    linkage_methods = ['ward', 'complete', 'average']

    for method in linkage_methods:
        for n_clusters in [3, 5, 8]:
            hc = AgglomerativeClustering(n_clusters=n_clusters, linkage=method)
            labels = hc.fit_predict(X)

            analysis = analyze_clusters(labels, cocktail_names, f'Hierarchical-{method}')

            title = f"{strategy_name} - Hierarchical {method} ({n_clusters} clusters)"
            filename = f"viz/clustering_exploration/{strategy_name}_{param_str}_hierarchical_{method}_k{n_clusters}.svg"
            create_visualization(X, labels, cocktail_names, title, filename, analysis)

            key = f"{method}_{n_clusters}"
            results[key] = {
                'labels': labels.tolist(),
                'analysis': analysis,
                'filename': filename
            }

            print(f"  Hierarchical {method} k={n_clusters}: {analysis['n_clusters']} clusters")

    return results

def run_spectral_analysis(X, cocktail_names, strategy_name, param_str, k_values=[3, 5, 8]):
    """Run spectral clustering."""
    results = {}

    for k in k_values:
        try:
            sc = SpectralClustering(n_clusters=k, random_state=42, affinity='nearest_neighbors')
            labels = sc.fit_predict(X)

            analysis = analyze_clusters(labels, cocktail_names, 'Spectral')

            title = f"{strategy_name} - Spectral Clustering k={k}"
            filename = f"viz/clustering_exploration/{strategy_name}_{param_str}_spectral_k{k}.svg"
            create_visualization(X, labels, cocktail_names, title, filename, analysis)

            results[k] = {
                'labels': labels.tolist(),
                'analysis': analysis,
                'filename': filename
            }

            print(f"  Spectral k={k}: {analysis['n_clusters']} clusters")
        except Exception as e:
            print(f"  Spectral k={k} failed: {e}")

    return results

def analyze_strategy(strategy_key, param=None, param_str=""):
    """Run comprehensive clustering analysis on a strategy."""
    print(f"\nAnalyzing: {strategy_key} {param_str}")
    print("="*60)

    # Get data points
    cocktail_names, X = get_cocktail_points(strategy_key, param)

    if X is None or len(X) == 0:
        print(f"  No data available for {strategy_key} {param_str}")
        return None

    print(f"  Found {len(X)} cocktails")

    results = {
        'strategy': strategy_key,
        'param': param,
        'param_str': param_str,
        'n_cocktails': len(X),
        'algorithms': {}
    }

    # Run different algorithms
    print("\n  Running K-Means...")
    results['algorithms']['kmeans'] = run_kmeans_analysis(
        X, cocktail_names, range(2, 11), strategy_key, param_str
    )

    print("\n  Running Mean Shift...")
    results['algorithms']['meanshift'] = run_meanshift_analysis(
        X, cocktail_names, strategy_key, param_str
    )

    print("\n  Running DBSCAN...")
    results['algorithms']['dbscan'] = run_dbscan_analysis(
        X, cocktail_names, strategy_key, param_str
    )

    print("\n  Running Hierarchical...")
    results['algorithms']['hierarchical'] = run_hierarchical_analysis(
        X, cocktail_names, strategy_key, param_str
    )

    print("\n  Running Spectral...")
    results['algorithms']['spectral'] = run_spectral_analysis(
        X, cocktail_names, strategy_key, param_str
    )

    return results

# Convert numpy arrays to lists for JSON serialization
def make_json_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        # Convert keys to strings if they're not JSON-serializable types
        return {
            (str(k) if not isinstance(k, (str, int, float, bool, type(None))) else
             (int(k) if isinstance(k, np.integer) else
              (float(k) if isinstance(k, np.floating) else k))):
            make_json_serializable(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj

# Main analysis execution
if __name__ == "__main__":
    # Load data and create output directory
    load_data()
    os.makedirs('viz/clustering_exploration', exist_ok=True)

    all_results = {}

    # 1. Analyze standard strategies
    print("\n" + "="*70)
    print("ANALYZING STANDARD STRATEGIES")
    print("="*70)

    for strategy in ['blend', 'role_slot', 'perceptual']:
        results = analyze_strategy(strategy, param_str=strategy)
        if results:
            all_results[strategy] = results

    # 2. Analyze blend_struct alpha spectrum
    print("\n" + "="*70)
    print("ANALYZING BLEND_STRUCT ALPHA SPECTRUM")
    print("="*70)

    # Focus on key alpha values mentioned by user
    key_alphas = ['a000', 'a015', 'a030', 'a055', 'a070', 'a085', 'a100']
    for alpha_str in key_alphas:
        strategy_key = f'blend_struct_{alpha_str}'
        alpha_val = int(alpha_str[1:]) / 100.0
        results = analyze_strategy(strategy_key, param_str=f"alpha_{alpha_val:.2f}")
        if results:
            all_results[strategy_key] = results

    # 3. Analyze tau (perceptual blend) spectrum
    print("\n" + "="*70)
    print("ANALYZING TAU (PERCEPTUAL BLEND) SPECTRUM")
    print("="*70)

    # Key tau values based on user observations
    key_taus = ['0.14', '0.383', '0.75', '4.019', '15.399', '115.478']
    for tau_val in key_taus:
        results = analyze_strategy('tau', param=tau_val, param_str=f"tau_{tau_val}")
        if results:
            all_results[f"tau_{tau_val}"] = results

    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)

    serializable_results = make_json_serializable(all_results)

    with open('viz/clustering_exploration/analysis_results.json', 'w') as f:
        json.dump(serializable_results, f, indent=2)

    print(f"\nGenerated {len(os.listdir('viz/clustering_exploration')) - 1} visualizations")
    print("Results saved to viz/clustering_exploration/analysis_results.json")
    print("\nAnalysis complete!")