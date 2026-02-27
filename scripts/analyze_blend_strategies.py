#!/usr/bin/env python3
"""
Analyze standard blend strategies (blend, perceptual, role_slot).
Part of parallel clustering analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.comprehensive_clustering_analysis import (
    analyze_strategy, make_json_serializable
)
import json

print("Starting analysis of standard blend strategies...")

results = {}

# Analyze standard strategies
strategies = [
    ('blend', None, 'blend'),
    ('role_slot', None, 'role_slot'),
    ('perceptual', None, 'perceptual')
]

for strategy, param, param_str in strategies:
    print(f"\nAnalyzing {strategy}...")
    result = analyze_strategy(strategy, param, param_str)
    if result:
        results[f"{strategy}_{param_str}"] = result
        print(f"✓ Completed {strategy}")

# Save results
output_file = 'viz/clustering_exploration/blend_strategies_results.json'
with open(output_file, 'w') as f:
    json.dump(make_json_serializable(results), f, indent=2)

print(f"\nResults saved to {output_file}")
print("Blend strategies analysis complete!")