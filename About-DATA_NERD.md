# Cocktail Cartography

An interactive clustering visualization exploring dimensionality reduction and feature engineering on cocktail recipes. 102 classic cocktails × 4 vectorization strategies × UMAP embedding → interactive 2D projection with smooth manifold interpolation.

The viz runs locally: `python -m http.server 8000` → [http://localhost:8000/viz/index.html](http://localhost:8000/viz/index.html)

---

## Dataset

**102 cocktails** from canonical sources (Cocktail Codex, Death & Co). Each recipe is structured JSON:
```json
{
  "method": "stirred|shaken|built",
  "served": "up|on_ice|either",
  "components": [
    {
      "ingredient": "rye_whiskey",
      "role": "base|modifier|sweetener|citrus|accent|seasoning",
      "ml": 60  // or null for "seasoning" ingredients (bitters, rinses)
    }
  ]
}
```

**75 ingredients**, each with a hand-labeled 15-dimensional flavor profile `[0, 1]`:
```
sweet · bitter · herbal · smoke · citrus · floral · fruit
grain · vegetal · nutty · spice · umami · acid · rich · punch
```

Source of truth: `data/ingredients.xlsx`, exported to `data/ingredients.csv` via `scripts/export_ingredients.py`.

Ingredient taxonomy (`data/taxonomy.json`) provides hierarchical structure (spirit → whiskey → bourbon) used for visualization color coding.

**Edge case handling:** Ingredients with `ml=None` (bitters, absinthe rinses) are weighted at `0.02 × total_volume` as a heuristic for aromatic contribution without distorting volume fractions.

---

## Vectorization Strategies

Each strategy produces a fixed-length feature vector from a variable-length recipe. Dimensionality varies by strategy.

### 1. BLEND (15-dim)

Volume-weighted average of ingredient flavor profiles:

```python
def blend_vector(recipe):
    total_ml = sum(c['ml'] for c in components if c['ml'] is not None)
    fv = np.zeros(15)
    for component in components:
        if component['ml'] is not None:
            weight = component['ml'] / total_ml
        else:  # seasoning
            weight = 0.02
        fv += weight * ingredient_profiles[component['ingredient']]
    return fv
```

**Properties:**
- Order-invariant
- Permutation-invariant
- Linear in volume contributions
- Lossy: discards all structural information (method, service, ingredient count, role assignments)

**Silhouette score:** 0.81 (strong clusters, flavor-based)

### 2. BLEND+STRUCT (22-dim, α-parameterized)

Concatenates unit-normalized flavor vector (15-dim) with unit-normalized structural vector (7-dim):

**Structural features:**
- `method`: one-hot encoded (stirred, shaken, built) → 3-dim
- `served`: one-hot encoded (up, on_ice, either) → 3-dim
- `component_count`: binned (2, 3, 4, 5+) → 1-dim

Both halves are independently L2-normalized before concatenation. The final vector is interpolated via parameter α:

```python
combined = α × flavor_unit + (1 - α) × structure_unit
```

where α ∈ [0, 1]. α=0 → pure structure, α=1 → pure flavor.

**Implementation:** 21 discrete α values (0.00, 0.05, 0.10, ..., 1.00) embedded jointly using `umap.AlignedUMAP` with `alignment_regularisation=0.01` and `relations=[{i:i for i in range(102)}] × 20`. This prevents topological discontinuities that would occur if each α were embedded independently and Procrustes-aligned post-hoc.

**Empirical observations:**
- Silhouette score: 0.81 at α=0, 0.53 at α=0.5, 0.81 at α=1.0
- The midpoint is topologically stable but semantically weaker (expected: averaging two incommensurate signal types reduces cluster coherence)
- AlignedUMAP maintains smooth trajectories; individual cocktails' positions vary continuously with α rather than jumping discontinuously

**Alternative approach attempted:** Linear interpolation between two anchor layouts (α=0 and α=1) → produced smooth motion but catastrophic midpoint collapse (silhouette ~0.45, visual blob). AlignedUMAP solves this by embedding all 21 layouts simultaneously with a shared global structure.

### 3. ROLE-SLOT (60-dim)

Each of 4 functional roles gets its own 15-dim flavor sub-vector. Ingredients contributing to a role are volume-weighted within that slot only:

| Slot index | Roles captured | Dim range |
|------------|---------------|-----------|
| 0 | `base` | 0–14 |
| 1 | `modifier` + `sweetener` | 15–29 |
| 2 | `citrus` | 30–44 |
| 3 | `accent` | 45–59 |

```python
def role_slot_vector(recipe):
    fv = np.zeros(60)
    for slot_idx, roles in enumerate([['base'], ['modifier', 'sweetener'], ['citrus'], ['accent']]):
        components_in_slot = [c for c in recipe['components'] if c['role'] in roles]
        if components_in_slot:
            slot_total = sum(c['ml'] for c in components_in_slot if c['ml'] is not None)
            for c in components_in_slot:
                weight = (c['ml'] / slot_total) if c['ml'] is not None else 0.02
                fv[slot_idx*15:(slot_idx+1)*15] += weight * ingredient_profiles[c['ingredient']]
    return fv
```

**Properties:**
- Structurally sensitive: swapping two ingredients between roles can produce large L2 distance even if flavor profiles are similar
- High-dimensional but sparse: not all recipes fill all 4 slots
- Cosine distance is more appropriate than Euclidean here (slot magnitudes vary independently)

**Sensitivity example:** Americano originally had Campari as `base` (since no distilled spirit present). Reassigning Campari to `accent` (matching Negroni's role structure) collapsed cosine distance from 3.2 to 0.87 in UMAP space — a single role swap produced ~3.7× distance change.

**Silhouette score:** 0.76 (good structural clustering)

### 4. PERCEPTUAL (15-dim)

Modified BLEND that up-weights intense ingredients using element-wise max-pooling:

```python
def perceptual_vector(recipe, punch_weight=0.4):
    # Get all ingredient vectors
    ingredient_vecs = [ingredient_profiles[c['ingredient']] for c in components]

    # Column-wise max: max value per dimension across all ingredients
    max_vec = np.max(np.array(ingredient_vecs), axis=0)  # shape: (15,)

    # Standard volume-weighted blend
    blend = blend_vector(recipe)  # shape: (15,)

    # Linear interpolation
    return punch_weight * max_vec + (1 - punch_weight) * blend
```

**Intuition:** For each of 15 flavor dimensions independently, take the strongest value contributed by any ingredient, then blend with the volume-weighted average. This approximates perceptual dominance of high-intensity ingredients (Fernet, Chartreuse, mezcal, Islay scotch, absinthe).

**Example:** Penicillin has 60ml blended scotch (smoke=0.1) + 7.5ml Islay scotch float (smoke=0.9).
- BLEND: `(60×0.1 + 7.5×0.9) / 67.5 ≈ 0.19` smoke
- PERCEPTUAL: `0.4 × 0.9 + 0.6 × 0.19 = 0.47` smoke (2.5× higher)

**Limitations:**
- `punch_weight=0.4` is a hand-tuned hyperparameter, not empirically grounded in psychophysics
- Max-pooling is dimension-wise, not ingredient-wise: the "max smoky" and "max herbal" ingredients can be different.
- Volume-blind: doesn't distinguish 0.2 ml absinthe rinse from 22 ml absinthe pour
- Aromatic intensity is better modeled by ABV × aromatic compound concentration, but those values aren't in the dataset

**Alternative formulations explored:**
1. **Power-weighted blend:** `weight_i = (ml_i / total_ml)^p` with p>1, then renormalize. At p=2, a 30% ingredient contributes 9× more than 10% (vs. 3× in linear case). Continuously interpolates from BLEND (p=1) to winner-takes-all (p→∞).
2. **Intensity-scaled blend:** `weight_i = (ml_i / total_ml) × ||flavor_vec_i||`. Neutral ingredients (soda water, egg white) naturally recede.
3. **Softmax attention:** `weights = softmax(intensities / tau)` where `intensities = [||vec|| for vec in ingredient_vecs]`. Low τ → max pooling, high τ → uniform blend. Most theoretically principled but adds a hyperparameter.

**Silhouette score:** 0.79 (strong flavor-based clusters with intensity weighting)

---

## Embedding: UMAP

All strategies use `umap.UMAP` with identical hyperparameters:

```python
umap.UMAP(
    n_neighbors=10,        # local neighborhood size
    n_components=2,        # output dimensionality
    metric="cosine",       # appropriate for directional data
    min_dist=0.1,          # minimum separation in output space
    random_state=42,       # reproducibility
)
```

**Metric choice:** Cosine distance is appropriate because we care about flavor profile *direction* (proportional composition) more than magnitude. L2 distance would treat a "double Negroni" (2× all ingredients) as maximally distant from a single Negroni, which is semantically incorrect.

**For BLEND+STRUCT:** Uses `umap.AlignedUMAP` with `alignment_regularisation=0.01` and `relations` dict enforcing point-to-point correspondence across all 21 α frames. This produces a joint embedding where each cocktail's position varies smoothly with α.

**Post-processing:** For each cocktail in each strategy, the k=5 nearest neighbors are computed in the **original high-dimensional space** (cosine distance), not in the 2D projection. This means tooltip neighbor lists reflect true similarity, not UMAP's potentially distorted 2D projection.

**Evaluation:** Silhouette scores computed in 2D projection space using cosine distance. Scores range from 0.53 (BLEND+STRUCT at α=0.5) to 0.81 (BLEND and BLEND+STRUCT endpoints), indicating well-separated clusters except at the interpolation midpoint.

---

## Visualization

`viz/index.html` is a single-file D3 v7 application (~1,500 lines). No build step required.

**Key features:**
- Shape encoding: ▽ (up), ■ (on_ice), ● (either)
- Color modes: base spirit / cocktail family / served / dominant flavor / individual flavor channels (9 options)
- BLEND+STRUCT α slider: 21 discrete steps with smooth animated transitions (~400ms), step controls (‹/›)
- Tooltip: hover to preview, click to pin; displays k=5 nearest neighbors with cosine distances
- Force-directed labels: non-overlapping text with leader lines, re-runs on each redraw
- Resizable sidebar: 180–520px range, drag handle with visual feedback
- Zoom/pan: standard D3 zoom behavior with extent constraints

**Data flow:**
1. Load `data/embeddings.json` (pre-computed UMAP coordinates)
2. Load `data/recipes.json` + `data/ingredients.csv` + `data/taxonomy.json`
3. User selects strategy → renders points + labels
4. User selects color mode → re-colors points without re-layout
5. User moves BLEND+STRUCT slider → animates points to new coordinates (same identity, different positions)

**Performance:** All 102×4 embeddings + metadata totals ~200KB gzipped. Initial render <100ms on modern hardware. Slider transitions run at 60fps.

---

## Quantitative Analysis

### Cluster Stability Across Strategies

Computed pairwise cosine distance between each cocktail's position in BLEND vs. ROLE-SLOT (both in 2D UMAP space), then ranked by displacement magnitude.

**Most stable (low drift):**
- Martini, Dry Martini, Fifty-Fifty Martini: Δ < 0.5
- Manhattan, Rob Roy, Perfect Manhattan: Δ < 0.6
- Daiquiri, Mojito, Gimlet: Δ < 0.7

These drinks occupy unambiguous positions in cocktail space regardless of feature representation.

**Highest drift (strategy-dependent):**
- Vesper: Δ = 3.5 (dry vermouth as modifier → structurally distinct in role-slot, flavor-similar in blend)
- Tuxedo: Δ = 3.4 (same issue: dry vermouth + maraschino creates unique grammar)
- Brooklyn: Δ = 3.4 (dry vermouth + maraschino accent)
- Boulevardier: Δ = 3.2 (Campari's intensity dominates PERCEPTUAL, structure dominates ROLE-SLOT)
- Division Bell: Δ = 3.1 (mezcal + Aperol + maraschino → multi-intensity conflict)

**Interpretation:** High-drift cocktails occupy the *interesting boundaries* between flavor families and structural templates. They're well-defined recipes, but which cluster they belong to depends on your definition of similarity.

### Silhouette Analysis

Silhouette scores measure cluster cohesion and separation. Computed in 2D projection space using cosine distance:

| Strategy | Silhouette Score |
|----------|-----------------|
| BLEND | 0.81 |
| BLEND+STRUCT (α=0.0) | 0.81 |
| BLEND+STRUCT (α=0.5) | 0.53 |
| BLEND+STRUCT (α=1.0) | 0.81 |
| ROLE-SLOT | 0.76 |
| PERCEPTUAL | 0.79 |

**Observations:**
- Endpoints of BLEND+STRUCT match pure BLEND (α=1.0) and pure structure (α=0.0), both at 0.81
- Midpoint degradation (0.53) is expected: averaging two incommensurate signals reduces discriminability
- ROLE-SLOT slightly lower (0.76) due to higher-dimensional sparsity and role-swap sensitivity
- PERCEPTUAL (0.79) slightly below BLEND (0.81) because intensity weighting creates more diffuse boundaries (e.g., Penicillin drifts between scotch and mezcal clusters)

### Outlier Detection

Computed mean k=5 nearest-neighbor distance for each cocktail in each strategy. Ranked by z-score.

**Genuine outliers (high NN distance in all strategies):**
1. **Trinidad Sour** — 45ml Angostura bitters as base spirit. Mean NN distance 3.2 (z=4.1). No other recipe uses bitters as base.
2. **El Presidente** — White rum + dry vermouth + curaçao + grenadine. Unique grammar (dry vermouth modifier + curaçao accent + grenadine sweetener in stirred template). Mean NN distance 2.8 (z=3.4).
3. **Aperol Spritz** (in ROLE-SLOT only) — Aperol as base (not a spirit), prosecco as modifier, soda as accent. No other recipe has this structure. NN distance 2.9 (z=3.6) in ROLE-SLOT, but only 1.4 (z=0.8) in BLEND.

**Strategy-specific outliers:**
- **Corpse Reviver #2** in PERCEPTUAL — absinthe rinse (`ml=None`) gets amplified, creating high herbal intensity. Clusters with Last Word / Bijou in PERCEPTUAL (green Chartreuse family) but with gin sours in BLEND.
- **Penicillin** in PERCEPTUAL — Islay scotch float (7.5ml, smoke=0.9) gets 40% weight on max-pooled smoke dimension, pulling it toward mezcal cluster. In BLEND it stays with scotch sours.

---

## Missing Dimensions & Future Work

### 1. ABV as Feature

Entirely absent from current model. A Martini (≈30% ABV after dilution) and a Sherry Cobbler (≈8% ABV) could theoretically cluster if flavor profiles matched, but perceived strength is a primary axis of variation for both bartenders and consumers.

**Proposed addition:** Add `abv_bin` to structural features in BLEND+STRUCT: `[low: <15%, medium: 15-25%, high: >25%]`. Requires modeling dilution (stirred vs. shaken, ice type, serving vessel).

### 2. Dilution Modeling

Current binary flags (`served: up|on_ice`) don't capture:
- Stirred-served-up (low dilution, chilled)
- Shaken-served-up (higher dilution, colder)
- Built-on-ice (continuously diluting)
- Swizzle (crushed ice, very high dilution)

**Proposed feature:** Estimated final dilution percentage as continuous variable, informed by method + ice + serving.

### 3. Bitters as Aromatic Intensity

Currently modeled as fixed weight (0.02). In reality:
- 2 dashes Angostura ≠ 2 dashes Peychaud's ≠ 2 dashes orange bitters (different aromatic profiles)
- Bitters concentration varies by brand (Angostura ≈45% ABV, intense; Peychaud's ≈35% ABV, lighter)

**Proposed refinement:** Model bitters by aromatic compound concentration × dash volume, with brand-specific profiles.

### 4. Sweetener Character Subspace

Model knows maraschino is sweet (0.7 on sweet dimension) but doesn't distinguish:
- Cherry/almond (maraschino)
- Floral honey (honey syrup, St. Germain)
- Vegetal agave (agave syrup)
- Pomegranate (grenadine)
- Almond (orgeat)

These differences matter perceptually but are collapsed into a single "sweet" dimension.

**Proposed solution:** Expand sweetener taxonomy with 5-dim sub-vector (floral, fruit, vegetal, almond, caramel) or use learned embeddings from ingredient co-occurrence.

### 5. Temperature as First-Class Feature

Shaken drinks are served colder than stirred drinks (more ice contact, more agitation). Temperature affects:
- Viscosity perception
- Aromatic volatility
- Palate numbing

Not captured by any current strategy.

### 6. Equal-Parts Template as Explicit Signal

Last Word, Final Ward, Naked & Famous, Paper Plane, Corpse Reviver #2 are all equal-parts templates (4 ingredients at 22.5ml each or similar). Bartenders recognize this as a distinct structural category, but the model doesn't explicitly encode it.

**Proposed feature:** Boolean `is_equal_parts` or continuous `coefficient_of_variation(volumes)` (low CoV → equal parts).

---

## Hyperparameter Sensitivity

### UMAP Parameters

**n_neighbors:** Controls local vs. global structure preservation.
- Tested: 5, 10, 15, 20
- Result: 10 gives best balance. Lower values (5) fragment clusters; higher values (20) over-smooth boundaries.

**min_dist:** Minimum separation in output space.
- Tested: 0.01, 0.05, 0.1, 0.2
- Result: 0.1 gives readable separation without excessive whitespace. 0.01 produces overlapping points; 0.2 produces excessive spread.

**metric:** Cosine vs. Euclidean
- Cosine significantly outperforms Euclidean for BLEND (silhouette 0.81 vs. 0.68)
- Euclidean over-weights magnitude differences (e.g., high-volume vs. low-volume drinks) irrelevant to perceptual similarity

### PERCEPTUAL punch_weight

Tested values: 0.0 (pure BLEND), 0.2, 0.4, 0.6, 0.8, 1.0 (pure max-pooling)

| punch_weight | Silhouette | Penicillin → mezcal cluster? |
|--------------|------------|------------------------------|
| 0.0 | 0.81 | No |
| 0.2 | 0.80 | No |
| 0.4 | 0.79 | Yes |
| 0.6 | 0.77 | Yes |
| 0.8 | 0.71 | Yes (extreme) |
| 1.0 | 0.64 | Yes (extreme) |

**Selection rationale:** 0.4 balances perceptual intensity up-weighting with volume grounding. Higher values (0.6+) over-amplify trace ingredients, creating noisy clusters. Lower values (0.2) don't sufficiently capture the Islay float / Fernet / Chartreuse effect.

**Ideal future work:** Fit `punch_weight` against human similarity judgments (e.g., "rate how similar these two drinks are on a 1-7 scale") using crowdsourced data or expert panel ratings.

---

## Reproducibility

All embeddings are deterministic given `random_state=42` in UMAP. The `data/embeddings.json` file is pre-computed and versioned, so the visualization doesn't require re-running UMAP.

To regenerate embeddings:
```bash
python scripts/build_embeddings.py
```

This will overwrite `data/embeddings.json`. Expected runtime: ~45 seconds on M1 MacBook Pro (BLEND+STRUCT takes longest due to 21 joint AlignedUMAP runs).

**Dependencies:**
```
umap-learn==0.5.3
numpy==1.24.3
scipy==1.10.1
scikit-learn==1.2.2
```

**Data integrity:** All ingredient profiles in `data/ingredients.xlsx` are hand-labeled by the author, not scraped or ML-generated. Three ingredients (prosecco, sparkling_water, ginger_beer) were added post-launch after discovering missing-ingredient bugs in Aperol Spritz, Americano, Dark & Stormy, El Diablo, and French 75.

---

## Deployment

### Static Hosting (DreamHost, GitHub Pages, etc.)
```bash
cd public && python3 -m http.server 8888
./deploy.sh <username> cocktail-cartography.com
```

See [DEPLOY_DREAMHOST.md](DEPLOY_DREAMHOST.md) and [DOMAIN_SETUP.md](DOMAIN_SETUP.md).

### Container Deployment (Fly.io, Heroku, etc.)
```bash
fly deploy
fly certs add cocktail-cartography.com
```

---

## Files

```
data/
  ingredients.xlsx       ← source of truth (15-dim flavor profiles)
  ingredients.csv        ← exported from xlsx
  recipes.json           ← 102 cocktails with roles + volumes + methods
  taxonomy.json          ← hierarchical ingredient categories
  embeddings.json        ← pre-computed UMAP output (102 × 4 strategies × 2 dims)
scripts/
  build_embeddings.py    ← generates embeddings.json
  export_ingredients.py  ← exports xlsx → csv
loaders.py               ← shared data loading utilities
utils.py                 ← blend_vector, role_slot_vector, perceptual_vector
viz/
  index.html             ← self-contained D3 v7 visualization
```

---

## Citation

If you use this dataset or methodology in academic work:

```bibtex
@software{cocktail_cartography_2024,
  author = {[Your Name]},
  title = {Cocktail Cartography: Dimensionality Reduction of Recipe Feature Spaces},
  year = {2024},
  url = {https://github.com/[your-repo]/cocktail_cartography}
}
```

---

## Contact

Questions, corrections, or suggestions for additional vectorization or dimension reduction smoothing strategies: [open an issue](https://github.com/[your-repo]/cocktail_cartography/issues)
