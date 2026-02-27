#!/usr/bin/env python3
"""
Compare blend strategy clustering with alpha=0 clustering
"""
import json
from pathlib import Path

def load_blend_clusters():
    """Load blend clustering from cluster_analysis.json"""
    with open('viz/cluster_analysis.json', 'r') as f:
        data = json.load(f)

    if 'blend' in data:
        return data['blend']['clusters']
    return {}

def load_alpha0_k8_clusters():
    """Load alpha=0 k=8 clustering"""
    with open('viz/clustering_exploration/alpha_spectrum_results.json', 'r') as f:
        data = json.load(f)

    clusters = {}
    if 'alpha_0.00' in data:
        alpha0 = data['alpha_0.00']
        if 'algorithms' in alpha0 and 'kmeans' in alpha0['algorithms']:
            kmeans = alpha0['algorithms']['kmeans']
            if 'results' in kmeans and 'k=8' in kmeans['results']:
                k8_data = kmeans['results']['k=8']
                if 'analysis' in k8_data and 'clusters' in k8_data['analysis']:
                    for cluster_id, cluster_data in k8_data['analysis']['clusters'].items():
                        clusters[cluster_id] = cluster_data.get('members', [])

    return clusters

def calculate_overlap(cluster1, cluster2):
    """Calculate Jaccard similarity between two clusters"""
    set1 = set(cluster1)
    set2 = set(cluster2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union

def main():
    blend_clusters = load_blend_clusters()
    alpha0_clusters = load_alpha0_k8_clusters()

    print("="*80)
    print("COMPARISON: BLEND vs ALPHA=0 K=8")
    print("="*80)

    # First show the basic stats
    print(f"\nBlend clustering: {len(blend_clusters)} clusters")
    for cluster_id, members in blend_clusters.items():
        print(f"  Cluster {cluster_id}: {len(members)} cocktails")

    print(f"\nAlpha=0 k=8 clustering: {len(alpha0_clusters)} clusters")
    for cluster_id, members in sorted(alpha0_clusters.items()):
        print(f"  Cluster {cluster_id}: {len(members)} cocktails")

    # Now find the best matches
    print("\n" + "="*80)
    print("CLUSTER MATCHING ANALYSIS")
    print("="*80)

    # For each alpha=0 cluster, find best matching blend cluster
    matches = []
    for alpha_id, alpha_members in sorted(alpha0_clusters.items()):
        best_match = None
        best_score = 0

        for blend_id, blend_members in blend_clusters.items():
            score = calculate_overlap(alpha_members, blend_members)
            if score > best_score:
                best_score = score
                best_match = (blend_id, blend_members)

        matches.append({
            'alpha_id': alpha_id,
            'alpha_members': alpha_members,
            'blend_id': best_match[0] if best_match else None,
            'blend_members': best_match[1] if best_match else [],
            'jaccard': best_score
        })

    # Print the matches
    for match in matches:
        print(f"\nAlpha=0 Cluster {match['alpha_id']} (n={len(match['alpha_members'])})")
        print(f"  Best match: Blend Cluster {match['blend_id']} (n={len(match['blend_members'])})")
        print(f"  Jaccard similarity: {match['jaccard']:.2%}")

        # Show the overlapping cocktails
        alpha_set = set(match['alpha_members'])
        blend_set = set(match['blend_members'])
        overlap = alpha_set & blend_set

        if overlap:
            print(f"  Overlapping cocktails ({len(overlap)}): {', '.join(sorted(list(overlap))[:10])}")
            if len(overlap) > 10:
                print(f"    ... and {len(overlap) - 10} more")

        # Show what's unique to each
        alpha_only = alpha_set - blend_set
        blend_only = blend_set - alpha_set

        if alpha_only:
            print(f"  Only in alpha=0 ({len(alpha_only)}): {', '.join(sorted(list(alpha_only))[:5])}")
            if len(alpha_only) > 5:
                print(f"    ... and {len(alpha_only) - 5} more")

        if blend_only:
            print(f"  Only in blend ({len(blend_only)}): {', '.join(sorted(list(blend_only))[:5])}")
            if len(blend_only) > 5:
                print(f"    ... and {len(blend_only) - 5} more")

    # Calculate overall similarity
    print("\n" + "="*80)
    print("OVERALL SIMILARITY")
    print("="*80)

    # Average Jaccard similarity
    avg_jaccard = sum(m['jaccard'] for m in matches) / len(matches) if matches else 0
    print(f"Average Jaccard similarity: {avg_jaccard:.2%}")

    # Interpretation
    if avg_jaccard > 0.7:
        print("CONCLUSION: Blend and Alpha=0 produce VERY SIMILAR groupings")
    elif avg_jaccard > 0.4:
        print("CONCLUSION: Blend and Alpha=0 produce MODERATELY SIMILAR groupings")
    else:
        print("CONCLUSION: Blend and Alpha=0 produce DIFFERENT groupings")

    print("\nNote: Blend has only 3 clusters while Alpha=0 k=8 has 8 clusters,")
    print("so we're comparing different granularities of clustering.")

if __name__ == "__main__":
    main()