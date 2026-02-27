# Cocktail Clustering Exploration

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

## Current Status

### Data Structure
- **102 cocktails** with recipe information in `data/embeddings.json`
- **4 main vectorization strategies** currently analyzed:
  - `blend` - Pure flavor profile (15-dim)
  - `role_slot` - Recipe grammar (60-dim)
  - `perceptual` - Intensity-weighted (15-dim)
  - `blend_struct_a050` - 50% structure + 50% flavor (22-dim)
- **Additional strategies available** but not yet analyzed:
  - `blend_struct_a000` through `blend_struct_a100` (21 positions total)
  - `tau` strategy (unexplored)

### Scripts Created

#### 1. `scripts/analyze_real_clusters.py`
- Performs k-means clustering on each strategy
- Finds optimal number of clusters using silhouette scoring
- Generates SVG visualizations with cluster boundaries
- Outputs:
  - `viz/kmeans_*.svg` - Visualizations for each strategy
  - `viz/cluster_analysis.json` - Cluster membership data

Current implementation:
- Tests k-means with 3-12 clusters
- Uses convex hulls for cluster boundaries
- Labels notable cocktails (hardcoded list of ~13)

#### 2. `scripts/generate_cluster_analysis.py` (deprecated)
- Earlier attempt with predetermined clusters
- Generated visualizations but with incorrect cluster assignments

### Analysis Page: `analysis.html`

Current features:
- Side-by-side layout with sticky images (45% width)
- Images stay visible while scrolling analysis text
- Click to zoom on visualizations
- Shows cluster members and descriptions

Issues identified by user:
- Cluster info boxes take up too much space
- Legend showing "Cluster 1, 2, 3" is not helpful
- Need more cocktail labels on visualizations
- Labels overlapping each other
- Want smoother cluster boundary curves
- Need cluster names directly on the visualization

## Key Findings So Far

### Clustering Results

1. **BLEND (Pure Flavor)**
   - K-means found 3 optimal clusters (silhouette: 0.598)
   - But user notes there may be subclusters worth exploring
   - Example: Whiskey Sour area might be distinct from Old Fashioned area

2. **ROLE-SLOT (Recipe Grammar)**
   - 4 optimal clusters (silhouette: 0.804) - highest score
   - Clear separation by structural templates
   - Old Fashioned family forms its own distinct cluster

3. **PERCEPTUAL (Intensity-Weighted)**
   - 3 optimal clusters (silhouette: 0.845) - clearest boundaries
   - Suggests this matches human perception best
   - Small intense ingredients dramatically affect clustering

4. **50/50 Mix**
   - 3 clusters (silhouette: 0.777)
   - Shows cocktails in transition between categories

### Notable Travelers

Cocktails that move between clusters reveal insights:

- **Boulevardier**:
  - BLEND: Clusters with whiskey drinks (Manhattan, Old Fashioned)
  - ROLE-SLOT: Clusters with Negroni (same template)
  - Reveals: Flavor says whiskey, structure says Negroni

- **Penicillin**:
  - Would normally be a citrus sour
  - Islay float pulls it to whiskey cluster in PERCEPTUAL
  - Shows how intensity overrides volume

- **Last Word**:
  - Sometimes with citrus sours
  - Sometimes with equal-parts templates
  - Chartreuse intensity can override structure

## User Feedback & Next Steps

### UI Improvements Needed

1. **Visualization improvements:**
   - Use smoother curves for cluster boundaries (not convex hulls)
   - Add cluster names directly on the plot
   - Remove unhelpful "Cluster 1, 2, 3" legend
   - Label more cocktails (~8-10 per cluster?)
   - Prevent label overlaps (force-directed or manual positioning)

2. **Layout tweaks:**
   - Make cluster info boxes more compact
   - Reduce extra spacing
   - Keep the sticky image behavior (user likes this)

### Analysis Expansion

1. **Analyze more strategies:**
   - User wants at least 8 different vectorization strategies
   - Explore the full `blend_struct` slider range
   - Look at subclusters within the large groups

2. **Subcluster analysis:**
   - Within the 43-cocktail "Citrus Sours", identify subclusters:
     - Last Word / Aperol Spritz area
     - Margarita / Gimlet / Mojito area
   - Within "Whiskey Territory", separate:
     - Whiskey Sour area
     - Old Fashioned / Boulevardier area
     - Manhattan area

3. **Traveler insights:**
   - Systematically identify cocktails that move between clusters
   - Document what each vectorization strategy reveals
   - Create a matrix showing which cocktails cluster together under different views

### Technical Improvements

1. **Clustering algorithm:**
   - Consider hierarchical clustering to find subclusters
   - Try different k values even if not "optimal" by silhouette
   - Possibly use DBSCAN for density-based clustering

2. **Visualization:**
   - Implement smooth spline curves for boundaries
   - Add force-directed label placement
   - Color cocktails by their cluster membership
   - Make cluster names descriptive (not just numbers)

## How to Resume Work

### File Structure
```
cocktail_cartography/
├── data/
│   ├── embeddings.json         # Main data file with all strategies
│   └── cluster_analysis.json   # Output from k-means analysis
├── scripts/
│   ├── analyze_real_clusters.py    # Main clustering script
│   └── generate_cluster_analysis.py # (deprecated)
├── viz/
│   ├── kmeans_*.svg            # Cluster visualizations
│   └── cluster_analysis.json   # Cluster membership data
├── analysis.html               # Current analysis page
└── docs/
    └── clustering-exploration.md # This file
```

### To Continue:

1. **Run clustering analysis:**
   ```bash
   source .venv/bin/activate
   python scripts/analyze_real_clusters.py
   ```

2. **View analysis page:**
   ```bash
   python -m http.server 8000
   # Navigate to http://localhost:8000/analysis.html
   ```

3. **Key improvements to make:**
   - Modify `analyze_real_clusters.py` to:
     - Try different k values (4-6 clusters for BLEND)
     - Add more cocktail labels
     - Implement smoother boundaries
     - Add cluster names to plot
   - Update `analysis.html` to:
     - Compact the cluster info boxes
     - Reduce spacing
     - Add analysis for more strategies

4. **Questions to explore:**
   - If you choose pure flavor, you accept Boulevardier is more like Old Fashioned than Negroni - what are the implications?
   - What defines the subclusters within the large citrus group?
   - Which cocktails are stable vs. travelers across all strategies?

## Next Context Window

When starting fresh, load:
1. This file for context
2. The About-COCKTAIL_DATA_NERD.md for analytical approach
3. Focus on expanding to 8+ strategies and finding meaningful subclusters
4. Implement the visualization improvements (smoother curves, better labels, cluster names on plot)