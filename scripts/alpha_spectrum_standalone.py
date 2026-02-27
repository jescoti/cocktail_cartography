#!/usr/bin/env python3
"""
Standalone analysis of blend_struct alpha spectrum.
Analyzes how clusters change from pure flavor (alpha=0) to pure structure (alpha=1).
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, MeanShift, DBSCAN, SpectralClustering, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from collections import defaultdict, Counter
import os
import warnings
warnings.filterwarnings('ignore')

# Load data
print("Loading cocktail data...")
with open('data/embeddings.json', 'r') as f:
    data = json.load(f)

# Create output directory
os.makedirs('viz/clustering_exploration', exist_ok=True)

def get_cocktail_points(strategy_key):
    """Get 2D points for a given strategy."""
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
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        if label >= 0:  # Skip noise points in DBSCAN
            clusters[label].append(cocktail_names[i])

    analysis = {
        'n_clusters': len(clusters),
        'clusters': {}
    }

    for cluster_id, members in clusters.items():
        analysis['clusters'][int(cluster_id)] = {
            'size': len(members),
            'members': members
        }

    return analysis

def analyze_strategy(strategy_key, alpha_value, description):
    """Run comprehensive clustering analysis on a strategy."""
    print(f"\nAnalyzing: {strategy_key} (alpha={alpha_value:.2f})")
    print("="*60)

    cocktail_names, X = get_cocktail_points(strategy_key)

    if X is None:
        print(f"  WARNING: Could not load data for {strategy_key}")
        return None

    print(f"  Found {len(cocktail_names)} cocktails")

    results = {
        'strategy': strategy_key,
        'alpha_value': alpha_value,
        'description': description,
        'n_cocktails': len(cocktail_names),
        'algorithms': {}
    }

    # 1. K-Means with different k values
    print("\n  Running K-Means...")
    kmeans_results = {}
    best_k = None
    best_silhouette = -1

    for k in range(2, 11):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        silhouette = silhouette_score(X, labels)

        kmeans_results[f'k={k}'] = {
            'n_clusters': k,
            'silhouette': float(silhouette),
            'analysis': analyze_clusters(labels, cocktail_names, f'KMeans k={k}')
        }

        print(f"  K-Means k={k}: {k} clusters, silhouette={silhouette:.3f}")

        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k

    results['algorithms']['kmeans'] = {
        'results': kmeans_results,
        'best_k': best_k,
        'best_silhouette': float(best_silhouette)
    }

    # 2. Mean Shift (finds natural number of clusters)
    print("\n  Running Mean Shift...")
    ms = MeanShift()
    labels = ms.fit_predict(X)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

    ms_analysis = analyze_clusters(labels, cocktail_names, 'Mean Shift')
    results['algorithms']['mean_shift'] = {
        'n_clusters': n_clusters,
        'analysis': ms_analysis
    }
    print(f"  Mean Shift: Found {n_clusters} clusters naturally")

    # 3. DBSCAN with different eps values
    print("\n  Running DBSCAN...")
    dbscan_results = {}

    for eps in [0.3, 0.5, 0.7, 1.0]:
        dbscan = DBSCAN(eps=eps, min_samples=3)
        labels = dbscan.fit_predict(X)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)

        dbscan_results[f'eps={eps}'] = {
            'eps': eps,
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'analysis': analyze_clusters(labels, cocktail_names, f'DBSCAN eps={eps}')
        }

        print(f"  DBSCAN eps={eps}: {n_clusters} clusters, {n_noise} outliers")

    results['algorithms']['dbscan'] = dbscan_results

    # 4. Hierarchical clustering
    print("\n  Running Hierarchical...")
    hierarchical_results = {}

    for linkage_method in ['ward', 'complete', 'average']:
        for k in [3, 5, 8]:
            hierarchical = AgglomerativeClustering(n_clusters=k, linkage=linkage_method)
            labels = hierarchical.fit_predict(X)

            hierarchical_results[f'{linkage_method}_k={k}'] = {
                'linkage': linkage_method,
                'n_clusters': k,
                'analysis': analyze_clusters(labels, cocktail_names,
                                           f'Hierarchical {linkage_method} k={k}')
            }

            print(f"  Hierarchical {linkage_method} k={k}: {k} clusters")

    results['algorithms']['hierarchical'] = hierarchical_results

    # 5. Spectral clustering
    print("\n  Running Spectral...")
    spectral_results = {}

    for k in [3, 5, 8]:
        spectral = SpectralClustering(n_clusters=k, random_state=42, affinity='nearest_neighbors')
        labels = spectral.fit_predict(X)

        spectral_results[f'k={k}'] = {
            'n_clusters': k,
            'analysis': analyze_clusters(labels, cocktail_names, f'Spectral k={k}')
        }

        print(f"  Spectral k={k}: {k} clusters")

    results['algorithms']['spectral'] = spectral_results

    return results

# Key alpha values to analyze
alpha_values = [
    ('a000', 0.00, "Pure flavor - user sees 8 clear clusters"),
    ('a015', 0.15, "Early structure emergence"),
    ('a030', 0.30, "5 clusters coalescing"),
    ('a055', 0.55, "Sweet spot - 3 hybrid clusters"),
    ('a070', 0.70, "Structure dominant"),
    ('a085', 0.85, "Heavy structure"),
    ('a100', 1.00, "Pure structure")
]

print("\n" + "="*70)
print("ANALYZING BLEND_STRUCT ALPHA SPECTRUM")
print("="*70)
print("\nThis analysis examines how clusters change as we blend")
print("flavor embeddings (alpha=0) with structural embeddings (alpha=1)")
print()

all_results = {}

for alpha_str, alpha_val, description in alpha_values:
    strategy_key = f'blend_struct_{alpha_str}'

    result = analyze_strategy(strategy_key, alpha_val, description)

    if result:
        all_results[f'alpha_{alpha_val:.2f}'] = result

        # Special notes for key alphas
        if alpha_val == 0.00:
            print("\n  *** ALPHA=0.00 ANALYSIS ***")
            print(f"  K-Means best k: {result['algorithms']['kmeans']['best_k']}")
            print(f"  Mean Shift found: {result['algorithms']['mean_shift']['n_clusters']} clusters")
            k8_result = result['algorithms']['kmeans']['results'].get('k=8')
            if k8_result:
                print(f"  K-Means k=8 silhouette: {k8_result['silhouette']:.3f}")
                print(f"  K-Means k=8 cluster sizes: {[c['size'] for c in k8_result['analysis']['clusters'].values()]}")

        elif alpha_val == 0.55:
            print("\n  *** ALPHA=0.55 'SWEET SPOT' ANALYSIS ***")
            print(f"  K-Means best k: {result['algorithms']['kmeans']['best_k']}")
            print(f"  Best silhouette: {result['algorithms']['kmeans']['best_silhouette']:.3f}")
            print(f"  Mean Shift found: {result['algorithms']['mean_shift']['n_clusters']} clusters")

# Save results
output_file = 'viz/clustering_exploration/alpha_spectrum_results.json'

def make_json_serializable(obj):
    """Convert numpy types to Python types for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj

with open(output_file, 'w') as f:
    json.dump(make_json_serializable(all_results), f, indent=2)

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

# Generate summary report
print("\nCluster Count Evolution Across Alpha Spectrum:")
print("-" * 60)
print(f"{'Alpha':<10} {'Best K-Means K':<18} {'Mean Shift':<15} {'Description'}")
print("-" * 60)

for alpha_str, alpha_val, description in alpha_values:
    key = f'alpha_{alpha_val:.2f}'
    if key in all_results:
        result = all_results[key]
        best_k = result['algorithms']['kmeans']['best_k']
        ms_clusters = result['algorithms']['mean_shift']['n_clusters']
        short_desc = description[:35]
        print(f"{alpha_val:<10.2f} {best_k:<18} {ms_clusters:<15} {short_desc}")

print("\n" + "="*70)
print(f"Results saved to: {output_file}")
print("Alpha spectrum analysis complete!")
print("="*70)
