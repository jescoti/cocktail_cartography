# Cocktail Clustering Analysis - Fresh Start Document

## The Big Picture: Why This Analysis Matters

### The Problem We're Solving

The main cocktail cartography visualization currently offers a slider with 21 positions, allowing users to smoothly transition between different ways of thinking about cocktail similarity. However:

- **Users find 21 positions overwhelming** - too many choices without clear purpose
- **Most intermediate positions aren't revelatory** - sliding from 35% to 40% structure doesn't reveal new insights
- **The interface lacks opinion** - it presents all options equally rather than guiding users to meaningful discoveries

**The core question:** Can we identify which views actually matter and simplify the interface to just those perspectives?

### The Goal

Create a data-driven analysis that:

1. **Identifies which vectorization strategies produce genuinely different clustering patterns** - not just slight variations
2. **Names and characterizes the meaningful clusters** - so users understand "Whiskey Territory" vs "Citrus Sours" rather than abstract dots
3. **Provides evidence for interface simplification** - recommend reducing from 21 slider positions to perhaps 4-6 radio buttons
4. **Reveals insights about cocktail relationships** - what does it mean when Boulevardier clusters with Manhattan vs Negroni?

### Why This Matters for Users

Right now, users can explore the visualization but may not understand:
- Why drinks cluster the way they do
- Which view to use for which purpose
- What the transitions actually reveal

By identifying and naming clusters, and reducing to meaningful views, we can make the tool more educational and useful for:
- **Cocktail discovery** - "If you like X, try Y from the same cluster"
- **Understanding cocktail theory** - "These drinks share a template despite different ingredients"
- **Recipe development** - "This new drink fits between these two clusters"

## Overview

This document summarizes the clustering analysis work done on the cocktail cartography dataset, including the tools developed, findings discovered, and next steps for refinement.
## Current State

We have generated 574 clustering visualizations across multiple embedding strategies (alpha spectrum, tau spectrum, standard strategies) using 5 different clustering algorithms. The visualizations exist but have issues with cluster naming and label readability.

### Key Files
- **Data source:** `data/embeddings.json` - Contains 102 cocktails with multiple embedding strategies
- **Visualizations:** `viz/clustering_exploration/` - 574 SVG files
- **Analysis results:**
  - `viz/clustering_exploration/alpha_spectrum_results.json`
  - `viz/clustering_exploration/tau_spectrum_results.json`
- **HTML reports:**
  - `clustering_analysis.html` - Initial comprehensive analysis
  - `clustering_analysis_revised.html` - Revised with corrections and carousels

### Confirmed Findings
1. **Alpha=0 shows 8 clusters** with k-means (silhouette=0.805) - human observation validated
2. **Alpha=0.55 is a convergence point** - K-means k=3, but Mean Shift finds 4
3. **Tau interpretation:** Low τ = intensity dominates, High τ = volume matters
4. **Whiskey Sour Island** emerges at tau=4.019 (5 cocktails: whiskey_sour, gold_rush, penicillin, brown_derby, lion_tail)

## Priority Tasks to Complete

### 1. Fix Cluster Naming
**Problem:** Current naming produces nonsense like "Chartreuse Complex" for cocktails without Chartreuse, "Agave-Based" for drinks with no agave. These are great names when ACCURATE, but nonsense in most of the ways they've been applied.

**Solution:**
- Extract actual cluster members from JSON files
- Analyze what's ACTUALLY in each cluster
- Use simple, descriptive names based on verified content
- Name according to common ingredients, common flavor components, or recipe archetypes
- Don't use "Martini Family" - The martini is distinct even if it's in the same cluster, so it's not the archetype. 
- When uncertain, ask the user for input.

### 2. Compare Blend k=8 vs Alpha=0 k=8
**Task:** Determine if regular "blend" strategy with k=8 produces the same groupings as alpha=0 (not visual similarity, but actual membership overlap).

**Method:**
```python
# Load both clustering results
blend_k8_clusters = load_blend_k8()
alpha0_k8_clusters = load_alpha0_k8()

# Compare membership overlap
for blend_cluster in blend_k8_clusters:
    for alpha_cluster in alpha0_k8_clusters:
        overlap = set(blend_cluster) & set(alpha_cluster)
        print(f"Overlap: {len(overlap)} cocktails")
```

### 3. Understand Perceptual Strategy
**Question:** What exactly is "perceptual" and does it match any specific tau value?

**Investigation needed:**
- Check `data/embeddings.json` for perceptual description
- Look for python code that generated the perceptual embeddings
- Compare perceptual clustering with various tau values
- Look for matching cluster structures
- Document the relationship (or lack thereof)

### 4. Extract Edge Cocktails for Innovation
**Goal:** Identify cocktails on cluster boundaries that could inspire new creations.

**Approach:**
- At alpha=0.70 (loose clustering), find cocktails equidistant from multiple cluster centers
- Identify "bridge" cocktails that appear in different clusters across strategies
- Map potential innovation paths between classic cocktails

### 5. Fix Visualizations
**Issues:**
- Labels overlapping or off-canvas
- "Weird little cluster of name labels" error
- Poor readability

**Solutions:**
- Generate ONE test visualization with perfect labels
- Verify output manually before mass production
- Ensure all labels stay within bounds
- Use force-directed label placement that actually works

## Implementation Order

### Phase 1: Data Audit (First Priority)
1. Load all JSON results files
2. Create a simple text report of what's in each cluster
3. Verify the whiskey sour island members
4. Compare blend vs alpha=0 memberships

### Phase 2: Fix Naming
1. Create a naming function that:
   - Lists actual members
   - Identifies common characteristics (stirred/shaken, base spirit, sour/bitter)
2. Look at the cluster members and try to come up with a name that accurately describes the cluster
3. Do this manually for the entire dataset. Do not outsource this to python, use your own judgement.

### Phase 3: Answer Key Questions
1. **Blend vs Alpha=0:** Quantify the overlap percentage
2. **Perceptual identity:** Determine its relationship to tau
3. **Edge cocktails:** Extract list of boundary cocktails

### Phase 4: Create Final Visualizations
1. Start with ONE perfect example (e.g., Alpha=0 k=8)
2. Verify labels are readable and accurate
3. Only then generate the key visualizations
4. Update HTML with verified, working images

## Data Structure Reference

### Embeddings Available
- `blend` - Pure ingredient blend
- `blend_struct_a000` through `blend_struct_a100` - Alpha spectrum (21 values)
- `tau` - Dictionary with keys like '0.14', '0.383', '0.75', '4.019', etc. (25 values)
- `perceptual` - Fixed perceptual weighting (punch_weight=0.4)
- `role_slot` - Recipe grammar/structure

### Clustering Results Structure
```json
{
  "strategy_name": {
    "algorithms": {
      "kmeans": {
        "k_value": {
          "analysis": {
            "clusters": {
              "cluster_id": {
                "all_members": ["cocktail_1", "cocktail_2", ...],
                "size": N,
                "name": "current_bad_name"
              }
            }
          }
        }
      }
    }
  }
}
```

## Verification Checklist

Before declaring any visualization complete:
- [ ] Print cluster members to console
- [ ] Verify the proposed name matches the content
- [ ] Open the SVG file and check labels are readable
- [ ] Ensure no overlapping text
- [ ] Confirm cluster boundaries enclose the right cocktails
- [ ] Test that labels stay within canvas bounds

## Expected Outcomes

1. **Cluster naming:** Simple, accurate names that reflect actual content
2. **Blend vs Alpha comparison:** Percentage overlap between groupings
3. **Perceptual identity:** Clear answer on its relationship to tau
4. **Edge cocktails:** List of 10-20 boundary cocktails for innovation
5. **Clean visualizations:** 5-10 key images with readable, accurate labels

## No-Gos

- Don't generate visualizations without checking them
- Don't use clever names without verifying content
- Don't assume algorithms are working - verify outputs
- Don't create 500+ files at once - start with one perfect example