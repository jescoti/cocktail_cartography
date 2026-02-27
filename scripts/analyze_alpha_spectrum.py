#!/usr/bin/env python3
"""
Analyze blend_struct alpha spectrum.
Part of parallel clustering analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.comprehensive_clustering_analysis import (
    analyze_strategy, make_json_serializable
)
import json

print("Starting analysis of blend_struct alpha spectrum...")

results = {}

# Key alpha values - including the ones you specifically mentioned
alpha_values = [
    ('a000', 0.00, "Pure flavor - you see 8 clear clusters"),
    ('a015', 0.15, "Early structure emergence"),
    ('a030', 0.30, "5 clusters coalescing"),
    ('a055', 0.55, "Sweet spot - 3 hybrid clusters"),
    ('a070', 0.70, "Structure dominant"),
    ('a085', 0.85, "Heavy structure"),
    ('a100', 1.00, "Pure structure")
]

for alpha_str, alpha_val, description in alpha_values:
    strategy_key = f'blend_struct_{alpha_str}'
    param_str = f"alpha_{alpha_val:.2f}"

    print(f"\nAnalyzing alpha={alpha_val:.2f} - {description}")
    result = analyze_strategy(strategy_key, None, param_str)

    if result:
        result['description'] = description
        result['alpha_value'] = alpha_val
        results[param_str] = result
        print(f"✓ Completed alpha={alpha_val:.2f}")

        # Special analysis for alpha=0 with k=8
        if alpha_val == 0.00:
            print("  Running special k=8 analysis as you observed 8 clusters...")
            # This is already included in the k range 2-10

# Save results
output_file = 'viz/clustering_exploration/alpha_spectrum_results.json'
with open(output_file, 'w') as f:
    json.dump(make_json_serializable(results), f, indent=2)

print(f"\nResults saved to {output_file}")
print("Alpha spectrum analysis complete!")