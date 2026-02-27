#!/usr/bin/env python3
"""
Analyze tau (perceptual blend) spectrum.
Part of parallel clustering analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.comprehensive_clustering_analysis import (
    get_cocktail_points, analyze_clusters, create_visualization,
    run_kmeans_analysis, run_meanshift_analysis, run_dbscan_analysis,
    run_hierarchical_analysis, run_spectral_analysis, make_json_serializable,
    load_data
)
import json
import numpy as np
import umap

print("Starting analysis of tau (perceptual blend) spectrum...")

# Load the data using shared function
data = load_data()

results = {}

# Key tau values based on your observations
tau_values = [
    ('0.14', "Small offshoots merge back in"),
    ('0.383', "3 clear groups (sour + 2 spirit-forward)"),
    ('0.75', "4 very clear clusters (2 sour, 2 spirit-forward)"),
    ('4.019', "Sours in middle, whiskey sour island emerges"),
    ('15.399', "Whiskey sour island persists"),
    ('115.478', "High tau - patterns stabilize")
]

def analyze_tau(tau_val, description):
    """Analyze a specific tau value."""
    print(f"\nAnalyzing tau={tau_val} - {description}")
    print("="*60)

    # Get tau embeddings
    if tau_val not in data['strategies']['tau']:
        print(f"  Warning: tau={tau_val} not found")
        return None

    tau_data = data['strategies']['tau'][tau_val]
    if 'embedding' not in tau_data:
        print(f"  Warning: No embeddings for tau={tau_val}")
        return None

    # Get embeddings for all cocktails
    embedding_data = tau_data['embedding']
    cocktail_names = list(embedding_data.keys())

    # Tau embeddings are already 2D projected (have x, y coordinates)
    X = np.array([[embedding_data[name]['x'], embedding_data[name]['y']]
                  for name in cocktail_names])

    print(f"  Found {len(cocktail_names)} cocktails")
    print("  Using pre-computed 2D projections...")

    param_str = f"tau_{tau_val}"
    strategy_name = f"tau_{tau_val}"

    result = {
        'tau_value': float(tau_val),
        'description': description,
        'n_cocktails': len(X),
        'algorithms': {}
    }

    # Run clustering algorithms
    print("  Running K-Means...")
    result['algorithms']['kmeans'] = run_kmeans_analysis(
        X, cocktail_names, range(2, 11), strategy_name, param_str
    )

    print("  Running Mean Shift...")
    result['algorithms']['meanshift'] = run_meanshift_analysis(
        X, cocktail_names, strategy_name, param_str
    )

    print("  Running DBSCAN...")
    result['algorithms']['dbscan'] = run_dbscan_analysis(
        X, cocktail_names, strategy_name, param_str
    )

    print("  Running Hierarchical...")
    result['algorithms']['hierarchical'] = run_hierarchical_analysis(
        X, cocktail_names, strategy_name, param_str
    )

    print("  Running Spectral...")
    result['algorithms']['spectral'] = run_spectral_analysis(
        X, cocktail_names, strategy_name, param_str
    )

    # Special analysis for tau=4.019 - look for whiskey sour island
    if tau_val == '4.019':
        print("\n  Special analysis: Looking for whiskey sour island...")

        # Check DBSCAN outliers
        for eps, dbscan_result in result['algorithms']['dbscan'].items():
            if 'analysis' in dbscan_result and 'outliers' in dbscan_result['analysis']:
                outliers = dbscan_result['analysis']['outliers']
                if 'whiskey_sour' in outliers:
                    print(f"    ✓ Whiskey Sour found as outlier with eps={eps}")
                    print(f"      Other outliers: {[o for o in outliers if o != 'whiskey_sour']}")

        # Check small clusters in k-means
        for k, kmeans_result in result['algorithms']['kmeans'].items():
            if 'analysis' in kmeans_result:
                for cluster_id, cluster_info in kmeans_result['analysis']['clusters'].items():
                    if 'whiskey_sour' in cluster_info['all_members'] and cluster_info['size'] <= 5:
                        print(f"    ✓ Whiskey Sour in small cluster (size {cluster_info['size']}) with k={k}")
                        print(f"      Cluster companions: {cluster_info['all_members']}")

    print(f"✓ Completed tau={tau_val}")
    return result

# Analyze each tau value
for tau_val, description in tau_values:
    result = analyze_tau(tau_val, description)
    if result:
        results[f"tau_{tau_val}"] = result

# Save results
output_file = 'viz/clustering_exploration/tau_spectrum_results.json'
with open(output_file, 'w') as f:
    json.dump(make_json_serializable(results), f, indent=2)

print(f"\nResults saved to {output_file}")
print("Tau spectrum analysis complete!")