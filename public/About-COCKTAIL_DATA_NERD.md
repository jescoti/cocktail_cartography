# Cocktail Cartography

An interactive clustering visualization of 102 classic cocktails, exploring dimensionality reduction and feature engineering on cocktail recipes. Shows how different ways of thinking about similarity produces different — and sometimes surprising — groupings through 4 vectorization strategies × UMAP embedding → interactive 2D projection with smooth manifold interpolation.

The viz runs locally: `python -m http.server 8000` → [http://localhost:8000/viz/index.html](http://localhost:8000/viz/index.html)

---

## What This Is

This project takes 102 classic cocktails and organizes them into visual clusters based on four different theories of similarity. You can switch between these views and watch drinks move around as the definition of "similar" changes.

The dataset includes everything from workhorses like Daiquiri (60ml white rum / 22.5ml lime / 15ml simple) and Manhattan (60ml rye / 30ml sweet vermouth / bitters) to oddities like Trinidad Sour (45ml Angostura as the base spirit) and equal-parts templates like Last Word and Paper Plane.

---

## Dataset Details

### Cocktails (102 total)
From canonical sources (Cocktail Codex, Death & Co). Each recipe is structured JSON:
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

### Ingredients (75 total)
Each with a hand-labeled 15-dimensional flavor profile `[0, 1]`:
```
sweet · bitter · saline · acid · herbal · spice · citrus · floral
fruit · smoke · oak · grain · vegetal · nutty · anise
```

Additional dimensions in some analyses:
```
umami · rich · punch
```

**Source of truth:** `data/ingredients.xlsx`, exported to `data/ingredients.csv` via `scripts/export_ingredients.py`.

**Ingredient taxonomy:** `data/taxonomy.json` provides hierarchical structure (spirit → whiskey → bourbon) used for visualization color coding.

**Edge case handling:** Ingredients with `ml=None` (bitters, absinthe rinses) are weighted at `0.02 × total_volume` as a heuristic for aromatic contribution without distorting volume fractions.

---

## The Four Ways of Grouping

### 1. BLEND: Pure Flavor Profile (15-dim)
Groups drinks by what they actually taste like, regardless of how they're built. Each ingredient has a flavor profile across 15 dimensions, and the drink's overall flavor is the weighted average based on volume.

**Implementation:**
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
- **Silhouette score:** 0.81 (strong clusters, flavor-based)

**What clusters well:**
- Daiquiri, Mojito, Caipirinha, Hemingway Daiquiri, Pisco Sour — refreshing lime-forward drinks
- Manhattan, Perfect Manhattan, Remember the Maine, Greenpoint, Little Italy — rye + sweet vermouth stirred drinks
- All the Martini variations stay tight together

**What splits apart:**
- Negroni and Manhattan don't cluster together, even though they're both "spirit + aromatized wine + modifier" structurally — they just taste completely different

### 2. BLEND+STRUCT: Flavor With a Structure Slider (22-dim, α-parameterized)
Adds structural information (stirred vs. shaken, served up vs. on ice, ingredient count) and lets you blend it with flavor using a slider. At one extreme it's pure structure, at the other it's pure flavor, and you can watch the map morph smoothly in between.

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
- AlignedUMAP maintains smooth trajectories; individual cocktails' positions vary continuously with α

**Worth watching:**
- Boulevardier starts near Negronis (same structure) and drifts toward whiskey Old Fashioneds (similar flavor) as you slide toward flavor
- Americano's journey — shares Campari + vermouth with Negroni but has soda water instead of gin, migrates between bitter aperitivo clusters and fizzy spritz territory
- Martinez (old tom gin / sweet vermouth / maraschino / bitters) moves between Negroni-land and Martini-land depending on whether you weight structure or flavor

### 3. ROLE-SLOT: Grammar Over Flavor (60-dim)
Treats each drink as having up to four functional slots: base spirit, modifying ingredients (vermouth/sweetener), citrus, and accent. Each slot gets its own 15-dimensional flavor sub-vector. Two drinks can taste similar but cluster far apart if the same flavors come from different structural positions.

**Slot allocation:**
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
- Structurally sensitive: swapping two ingredients between roles can produce large L2 distance
- High-dimensional but sparse: not all recipes fill all 4 slots
- Cosine distance is more appropriate than Euclidean
- **Silhouette score:** 0.76 (good structural clustering)

**Sensitivity example:** Americano originally had Campari as `base` (since no distilled spirit). Reassigning Campari to `accent` (matching Negroni's role structure) collapsed cosine distance from 3.2 to 0.87 in UMAP space — a single role swap produced ~3.7× distance change.

**What this captures:**
- Negroni, Boulevardier, Old Pal, Mezcal Negroni, White Negroni — all equal-parts "base + modifier + accent" templates
- All the sours (Daiquiri, Whiskey Sour, Margarita, etc.) cluster together because they're all "base + citrus + sweetener"
- Manhattan variants (Rob Roy with scotch, Black Manhattan with Averna) stay together

**What breaks:**
- Drinks with unusual slot-filling. Martinez has maraschino as an accent, making its grammar look more like Negroni than Martini

### 4. PERCEPTUAL: Intensity-Weighted Flavor (15-dim)
Like BLEND, but amplifies ingredients that punch above their weight. A Penicillin has 60ml blended scotch and 7.5ml Islay scotch as a float — the Islay is only ~11% by volume but it's the entire personality of the drink. Same with Fernet in a Hanky Panky, green Chartreuse in a Bijou, or the absinthe rinse in a Sazerac.

**Implementation:**
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

**Example:** Penicillin has 60ml blended scotch (smoke=0.1) + 7.5ml Islay scotch float (smoke=0.9).
- BLEND: `(60×0.1 + 7.5×0.9) / 67.5 ≈ 0.19` smoke
- PERCEPTUAL: `0.4 × 0.9 + 0.6 × 0.19 = 0.47` smoke (2.5× higher)

**Properties:**
- `punch_weight=0.4` is hand-tuned, not empirically grounded
- Max-pooling is dimension-wise, not ingredient-wise
- Volume-blind: doesn't distinguish 0.2ml absinthe rinse from 22ml absinthe pour
- **Silhouette score:** 0.79 (strong flavor-based clusters with intensity weighting)

**What this gets right:**
- Penicillin clusters closer to smoky mezcal drinks than to regular scotch sours
- Hanky Panky (gin + vermouth + Fernet) clusters near other Fernet-forward drinks
- Aperol Spritz ends up near Adonis and El Presidente (light, wine-forward, gently bitter)

**What it can't fully capture:**
- A 2ml absinthe rinse vs. 22ml of absinthe as a full pour — the model up-weights both equally

**Alternative formulations explored:**
1. **Power-weighted blend:** `weight_i = (ml_i / total_ml)^p` with p>1
2. **Intensity-scaled blend:** `weight_i = (ml_i / total_ml) × ||flavor_vec_i||`
3. **Softmax attention:** `weights = softmax(intensities / tau)`

---

## Embedding Technical Details: UMAP

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

**Post-processing:** For each cocktail, the k=5 nearest neighbors are computed in the **original high-dimensional space** (cosine distance), not in the 2D projection. Tooltip neighbor lists reflect true similarity, not UMAP's potentially distorted 2D projection.

---

## Interesting Findings

### Stable Cores
Some drinks barely move across all four strategies — they're unambiguous classics that define their categories:
- Martini variations (Martini, Fifty-Fifty, Vesper) always cluster together (Δ < 0.5)
- The Manhattan family (Manhattan, Rob Roy, Perfect Manhattan) stays coherent (Δ < 0.6)
- Classic simple sours (Daiquiri, Gimlet, Margarita) cluster reliably (Δ < 0.7)

### The Travelers
These drinks visit wildly different neighborhoods depending on strategy:

**Boulevardier** (bourbon / sweet vermouth / Campari) — In structure view it's with Negronis. In flavor view it drifts toward whiskey-vermouth drinks. It occupies the boundary between bitter aperitivo territory and Manhattan-land. (Δ = 3.2)

**Aviation** (gin / lemon / maraschino / crème de violette) — The maraschino dominates in perceptual view, grouping it with Last Word and Hemingway Daiquiri. In volume-weighted view, the gin takes over and it becomes a gin sour.

**Corpse Reviver #2** (equal parts gin / lemon / Cointreau / Lillet + absinthe rinse) — In perceptual view the absinthe rinse has outsized influence. In role-slot view it's an equal-parts drink. In pure flavor view it's just a gin sour. Each is defensible.

**Vesper** (Δ = 3.5) — Dry vermouth as modifier makes it structurally distinct in role-slot, flavor-similar in blend

**Tuxedo** (Δ = 3.4) — Dry vermouth + maraschino creates unique grammar

**Division Bell** (Δ = 3.1) — Mezcal + Aperol + maraschino creates multi-intensity conflict

### Genuine Outliers

**Trinidad Sour** — Absolutely isolated in every strategy. It's a sour template but with 45ml Angostura bitters as the base spirit. Nothing else in the canon does this. Mean NN distance 3.2 (z=4.1).

**El Presidente** (white rum / dry vermouth / curaçao / grenadine) — The only drink with dry vermouth as modifier, curaçao as accent, and grenadine as sweetener in a stirred build. Its grammar is genuinely unique. Mean NN distance 2.8 (z=3.4).

**Aperol Spritz** in role-slot view — It has Aperol as the base (not a spirit), which makes it structurally unlike anything else. NN distance 2.9 (z=3.6) in ROLE-SLOT, but only 1.4 (z=0.8) in BLEND.

### Base Spirit Drift
One of the most visible axes across all strategies is base spirit, even though we never explicitly told the model "gin vs. whiskey matters." The flavor profiles naturally separate:
- Gin clusters (juniper, floral, herbal)
- Whiskey clusters (oak, grain, spice)
- Rum clusters (fruit, lighter body)
- Agave clusters (vegetal, earthy)

But the *boundaries* between these clusters change. In BLEND, an Aviation can drift toward whiskey territory if the maraschino and violette pull it away from juniper. In PERCEPTUAL, anything with intense smoky mezcal or Islay scotch groups together regardless of the base spirit category.

---

## Quantitative Analysis

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
- Endpoints of BLEND+STRUCT match pure BLEND (α=1.0) and pure structure (α=0.0)
- Midpoint degradation (0.53) is expected: averaging two incommensurate signals reduces discriminability
- ROLE-SLOT slightly lower (0.76) due to higher-dimensional sparsity and role-swap sensitivity
- PERCEPTUAL (0.79) slightly below BLEND (0.81) because intensity weighting creates more diffuse boundaries

### Hyperparameter Sensitivity

#### UMAP Parameters

**n_neighbors:** Controls local vs. global structure preservation.
- Tested: 5, 10, 15, 20
- Result: 10 gives best balance. Lower values fragment clusters; higher values over-smooth boundaries.

**min_dist:** Minimum separation in output space.
- Tested: 0.01, 0.05, 0.1, 0.2
- Result: 0.1 gives readable separation without excessive whitespace.

**metric:** Cosine vs. Euclidean
- Cosine significantly outperforms Euclidean for BLEND (silhouette 0.81 vs. 0.68)
- Euclidean over-weights magnitude differences irrelevant to perceptual similarity

#### PERCEPTUAL punch_weight

Tested values: 0.0 (pure BLEND), 0.2, 0.4, 0.6, 0.8, 1.0 (pure max-pooling)

| punch_weight | Silhouette | Penicillin → mezcal cluster? |
|--------------|------------|------------------------------|
| 0.0 | 0.81 | No |
| 0.2 | 0.80 | No |
| 0.4 | 0.79 | Yes |
| 0.6 | 0.77 | Yes |
| 0.8 | 0.71 | Yes (extreme) |
| 1.0 | 0.64 | Yes (extreme) |

**Selection rationale:** 0.4 balances perceptual intensity up-weighting with volume grounding.

---

## What's Missing & Future Work

### 1. ABV as Feature
Entirely absent from current model. A Vesper (high-proof) and a Sherry Cobbler (low-ABV) could theoretically cluster if flavor profiles matched, but no bartender would recommend them as substitutes. Strength is one of the first filters people use.

**Proposed addition:** Add `abv_bin` to structural features: `[low: <15%, medium: 15-25%, high: >25%]`.

### 2. Dilution Modeling
Current binary flags (`served: up|on_ice`) don't capture:
- Stirred-served-up (low dilution, chilled)
- Shaken-served-up (higher dilution, colder)
- Built-on-ice (continuously diluting)
- Swizzle (crushed ice, very high dilution)

**Proposed feature:** Estimated final dilution percentage as continuous variable.

### 3. Bitters as Aromatic Intensity
Currently modeled as fixed weight (0.02). In reality:
- 2 dashes Angostura ≠ 2 dashes Peychaud's ≠ 2 dashes orange bitters
- Bitters concentration varies by brand (Angostura ≈45% ABV, Peychaud's ≈35% ABV)

**Proposed refinement:** Model bitters by aromatic compound concentration × dash volume.

### 4. Sweetener Character Subspace
Model knows maraschino is sweet but doesn't distinguish:
- Cherry/almond (maraschino)
- Floral honey (honey syrup, St. Germain)
- Vegetal agave (agave syrup)
- Pomegranate (grenadine)
- Almond (orgeat)

**Proposed solution:** Expand sweetener taxonomy with 5-dim sub-vector or use learned embeddings.

### 5. Temperature as First-Class Feature
Shaken drinks are served colder than stirred drinks. Temperature affects viscosity perception, aromatic volatility, and palate numbing. Not captured by any current strategy.

### 6. Equal-Parts Template as Explicit Signal
Last Word, Final Ward, Naked & Famous, Paper Plane, Corpse Reviver #2 are all equal-parts templates. Bartenders recognize this as a distinct structural category, but the model doesn't explicitly encode it.

**Proposed feature:** Boolean `is_equal_parts` or continuous `coefficient_of_variation(volumes)`.

---

## Recipes You Might Debate

All recipes come from Cocktail Codex, Death & Co, and similar canon sources, but there's always room for interpretation:

**Negroni:** 30ml gin / 30ml sweet vermouth / 30ml Campari (equal parts, served on ice)
- Some bartenders do 1.25:1:1 to let the gin lead

**Martini:** 75ml gin / 15ml dry vermouth / orange bitters (5:1 ratio, served up)
- The classic midcentury ratio; modern "dry" Martinis can be 10:1 or higher

**Daiquiri:** 60ml white rum / 22.5ml lime / 15ml simple (~4:1.5:1)
- Some prefer 2:1:1 for a sharper drink

**Old Fashioned:** 60ml bourbon / 7.5ml demerara syrup / Angostura
- Sugar cube vs. syrup is an eternal debate

**Last Word:** 22.5ml each of gin, lime, maraschino, green Chartreuse (equal parts)
- Zero wiggle room here — it's definitionally equal parts

If you think a recipe is wrong, you're probably not wrong — you're just working from a different canonical source. The clustering will shift if you change ratios, but the overall structure holds.

---

## Visualization Technical Details

`viz/index.html` is a single-file D3 v7 application (~1,500 lines). No build step required.

**Key features:**
- Shape encoding: ▽ (up), ■ (on_ice), ● (either)
- Color modes: base spirit / cocktail family / served / dominant flavor / individual flavor channels (9 options)
- BLEND+STRUCT α slider: 21 discrete steps with smooth animated transitions (~400ms)
- Tooltip: hover to preview, click to pin; displays k=5 nearest neighbors with cosine distances
- Force-directed labels: non-overlapping text with leader lines, re-runs on each redraw
- Resizable sidebar: 180–520px range, drag handle with visual feedback
- Zoom/pan: standard D3 zoom behavior with extent constraints

**Data flow:**
1. Load `data/embeddings.json` (pre-computed UMAP coordinates)
2. Load `data/recipes.json` + `data/ingredients.csv` + `data/taxonomy.json`
3. User selects strategy → renders points + labels
4. User selects color mode → re-colors points without re-layout
5. User moves BLEND+STRUCT slider → animates points to new coordinates

**Performance:** All 102×4 embeddings + metadata totals ~200KB gzipped. Initial render <100ms on modern hardware. Slider transitions run at 60fps.

---

## Setup & Reproducibility

```bash
python -m venv .venv
source .venv/bin/activate
pip install umap-learn numpy scipy openpyxl scikit-learn

# Build embeddings (deterministic with random_state=42)
python scripts/build_embeddings.py

# Serve viz locally
python -m http.server 8000
# → open http://localhost:8000/viz/index.html
```

**Dependencies:**
```
umap-learn==0.5.3
numpy==1.24.3
scipy==1.10.1
scikit-learn==1.2.2
```

To regenerate embeddings:
```bash
python scripts/build_embeddings.py
```
Expected runtime: ~45 seconds on M1 MacBook Pro (BLEND+STRUCT takes longest due to 21 joint AlignedUMAP runs).

**Data integrity:** All ingredient profiles in `data/ingredients.xlsx` are hand-labeled by the author, not scraped or ML-generated. Three ingredients (prosecco, sparkling_water, ginger_beer) were added post-launch after discovering missing-ingredient bugs.

---

## Deployment

### Static Hosting (DreamHost, GitHub Pages, etc.)
```bash
cd public && python3 -m http.server 8888
./deploy.sh <username> cocktail-cartography.com
```

### Container Deployment (Fly.io, Heroku, etc.)
```bash
fly deploy
fly certs add cocktail-cartography.com
```

See [DEPLOY_DREAMHOST.md](DEPLOY_DREAMHOST.md) and [DOMAIN_SETUP.md](DOMAIN_SETUP.md) for details.

---

## Data Files

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