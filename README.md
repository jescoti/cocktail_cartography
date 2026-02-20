# Cocktail Cartography

An interactive clustering visualization of 102 classic cocktails, using UMAP dimensionality reduction to explore how different ways of representing a cocktail's character produce different — and sometimes surprising — groupings.

The viz runs locally: `python -m http.server 8000` → [http://localhost:8000/viz/index.html](http://localhost:8000/viz/index.html)

---

## Part I: Technical Overview

### The Data

**102 cocktails** drawn from classic canon (Cocktail Codex families, Death & Co, and related sources). Each recipe encodes:
- Ingredients with volumes (ml) and functional roles (`base`, `modifier`, `sweetener`, `citrus`, `accent`, `seasoning`)
- Method (`stirred`, `shaken`, `built`)
- Service (`up`, `on_ice`, `either`)

**75 ingredients**, each with a 15-dimensional flavor profile hand-encoded on a `[0, 1]` scale:

```
sweet · bitter · herbal · smoke · citrus · floral · fruit
grain · vegetal · nutty · spice · umami · acid · rich · punch
```

The ingredient profiles live in `data/ingredients.xlsx` (source of truth), exported to `data/ingredients.csv` via `scripts/export_ingredients.py`. The taxonomy in `data/taxonomy.json` provides hierarchical categories (spirit → whiskey → bourbon, etc.) used by the visualization for color coding and family-highlight filtering.

Three ingredients were added during development that were missing from the original dataset: **prosecco**, **sparkling_water**, and **ginger_beer** — discovered when Aperol Spritz, Americano, Dark & Stormy, El Diablo, and French 75 were all rendering as single-ingredient drinks.

---

### The Vectorization Strategies

Four strategies convert each recipe into a fixed-length vector, each capturing a different theory of what makes cocktails similar.

#### 1. BLEND (15-dim)
A pure **flavor fingerprint**: each ingredient's 15-dim profile is weighted by its proportion of total volume in the drink, then summed. The result is a single vector representing "what this drink tastes like in aggregate, regardless of how it's structured."

```python
fv = sum(profile[ing] * (ml / total_ml) for ing, ml in components)
```

Seasoning-role ingredients (bitters, absinthe rinses) with `ml=None` are included at a small fixed weight (0.02) to acknowledge their aromatic contribution without distorting volume fractions.

#### 2. BLEND+STRUCT (22-dim, α-blended)
Extends BLEND with a **7-dim structural vector** capturing method (stirred/shaken/built), service (up/on_ice/either), and component-count bins. Both halves are independently unit-normalized before concatenation, then interpolated:

```
combined = α × flavor_unit + (1-α) × structure_unit
```

The α slider in the viz (0 = pure structure, 1 = pure flavor) is implemented via **AlignedUMAP**: all 21 α-steps (0.00 → 1.00 at 0.05 increments) are jointly embedded with an alignment penalty (`alignment_regularisation=0.01`), ensuring smooth, topologically stable transitions rather than 21 independently-solved layouts that would jump discontinuously.

This was a non-trivial engineering challenge. Earlier approaches tried:
- 21 independent UMAP runs + Procrustes alignment → topology flips caused irreducible jumping
- Linear interpolation of two anchor layouts → smooth positions but the midpoint collapsed into a blob (silhouette ~0.45, vs. 0.81 at the endpoints)

AlignedUMAP solved both problems: silhouette score stays ≥ 0.53 across all steps, and positions move smoothly.

#### 3. ROLE-SLOT (60-dim)
Treats a cocktail as **grammar** rather than flavor. Each of 4 functional slots gets its own 15-dim flavor sub-vector:

| Slot | Roles captured |
|------|---------------|
| base | `base` |
| modifying | `modifier` + `sweetener` |
| citrus | `citrus` |
| accent | `accent` |

Ingredients within a slot are volume-weighted and summed within that slot only. The 4 sub-vectors are concatenated to form the full 60-dim representation.

This means two drinks can have very similar flavors but land far apart if those flavors come from different structural positions — and vice versa. The Negroni and Americano are an instructive example: they cluster together here precisely because campari plays the `accent` role in both. However, whenthe Americano recipe was initially composed with campari as `base`, it produced a significant distance between two otherwise similar drinks. Correcting this collapsed the distance to 0.87 in UMAP space, but the impact of this small change illustrates the brittleness of this method.

#### 4. PERCEPTUAL (15-dim)
A modified BLEND that **down-weights neutral filler ingredients** and **amplifies the most intense components**. A `punch_weight` parameter (0.4) re-balances contributions by flavor intensity rather than pure volume. This gives more influence to high-proof, bold-flavored accents relative to large-volume but neutral components like soda water or ice-diluted juice.

**The formula (lines 194–198):**
```python
stacked = np.array(ingredient_vecs)   # shape: (n_ingredients, 15)
max_vec  = stacked.max(axis=0)        # column-wise max: shape (15,)
blend    = blend_vector(recipe)       # volume-weighted average: shape (15,)

return PUNCH_WEIGHT * max_vec + (1 - PUNCH_WEIGHT) * blend
# = 0.4 × max_vec + 0.6 × blend
```

For each of the 15 flavor dimensions independently, it takes the per-column maximum across all ingredients in the drink, then linearly blends that with the normal volume-weighted average (40/60 split).

**What this actually means**
The `max_vec` records the highest value any single ingredient contributes to each flavor channel — regardless of volume. So if a drink has 60ml gin (smoke=0.0) and 7.5ml islay scotch (smoke=0.9), the `max_vec` smoke dimension is 0.9. In the plain BLEND, islay scotch contributes only `7.5/67.5 × 0.9 ≈ 0.10`. Perceptual gives it `0.4 × 0.9 + 0.6 × 0.10 = 0.42` — four times more weight. This is the model's approximation of how aromatic intensity, proof, and volatility let minor-volume ingredients dominate perception. Fernet Branca, green chartreuse, mezcal, absinthe, and islay scotch all benefit from this. Large-volume but neutral ingredients (soda water, prosecco, egg white, lime juice) lose relative influence.

**Why the max operation makes sense**
The `max_vec` is taken per dimension independently, not per ingredient. Initially this might seem wrong — the "max smoky" ingredient and the "max herbal" ingredient might be completely different, creating a vector that no single ingredient possesses. But this is actually the point: when you taste a cocktail, you don't taste ingredients sequentially — you taste the unified expression of all their strongest contributions simultaneously. A drink with smoky mezcal, herbal green chartreuse, and spicy rye expresses all three characteristics at once. The max operation captures this perceptual ceiling for each flavor channel in the finished drink.

The real limitation is more mundane: volume still matters. A drop of mezcal in a mostly-vodka drink doesn't make it as smoky as a proper mezcal cocktail, even if mezcal's smoke value is 0.9 in both cases. The `max_vec` is volume-blind, so it can't distinguish between "a trace of smoke" and "smoke as a defining character." That's what the 60/40 blend with the volume-weighted average compensates for — anchoring the signal so that a 2ml rinse of absinthe doesn't make a drink as aggressively herbal as one where absinthe is a full 22ml pour. The 40/60 split `(PUNCH_WEIGHT = 0.4)` was chosen manually, not tuned against human perception data.

**What it doesn't capture**
The perceptual insight it's gesturing at — that 7.5ml of Fernet "punches above its weight" — is real, but the mechanism it's modeling is really aromatic intensity × volatility, not just max(flavor_value). A proper model would weight each ingredient by something like its aromatic compound concentration or proof level. Those values aren't in the dataset, so the max-pooling is a structural proxy for the same idea.

**Alternative transformations to explore**
The current linear mix `(0.4 × max + 0.6 × blend)` is a blunt instrument. Several more principled approaches could better capture the interplay between volume and intensity:

1. **Power-weighted blend** — Instead of linear volume weighting, raise each ingredient's proportion to a power > 1 before normalizing:
   ```python
   weights = (ml_i / total_ml) ** p   # p=2 or p=3, then renormalize
   ```
   At p=1 you get BLEND. As p → ∞ you approach "winner takes all." At p=2, something at 30% of the drink contributes 9x more than something at 10%, versus 3x in the linear case.

2. **Intensity-scaled blend** — Weight each ingredient by volume × flavor_norm rather than volume alone:
   ```python
   intensity = np.linalg.norm(flavor_vec)
   weight = (ml_i / total_ml) * intensity
   ```
   Neutral ingredients (soda water, egg white) naturally recede; intense ones (Campari, green chartreuse) punch up.

3. **Softmax over ingredients** — Treat flavor intensity as a temperature-scaled attention mechanism:
   ```python
   intensities = [np.linalg.norm(vec) for vec in ingredient_vecs]
   weights = softmax(np.array(intensities) / tau)
   ```
   Low τ → the most intense ingredient dominates; high τ → equal weights. This elegantly interpolates between max (τ→0) and uniform blend (τ→∞) with a single parameter, more principled than the ad-hoc 0.4/0.6 split.

Of these, the softmax approach is probably most theoretically sound — it captures the idea that volume and intensity interact multiplicatively, with a tunable parameter controlling how much intense ingredients dominate perception.

---

### The Embedding

All strategies use the same UMAP parameters:

```python
umap.UMAP(
    n_neighbors=10,
    n_components=2,
    metric="cosine",
    min_dist=0.1,
    random_state=42,
)
```

Cosine metric is appropriate here because we care about the *direction* of a flavor profile (what proportions are present) more than its magnitude.

For BLEND+STRUCT, `umap.AlignedUMAP` is used with `relations=[{i:i for i in range(102)}] × 20`, meaning every point in every α-frame is declared to correspond to the same physical cocktail. The alignment penalty gently discourages large inter-frame moves without forcing rigidity.

**Post-processing:** For each strategy, the top-5 nearest neighbors per cocktail are computed in the original high-dimensional space (cosine distance), not in the 2D projection. This means the tooltip's neighbor list reflects true high-dimensional similarity, not just 2D visual proximity (which can be distorted by UMAP's nonlinear projection).

---

### The Visualization

`viz/index.html` is a single-file D3 v7 application (~1,500 lines):

- **Dot shapes**: ▽ = served up, ■ = on ice, ● = either
- **Color dimensions**: base spirit, cocktail family, served, dominant flavor, or any of 9 individual flavor channels (sweet, bitter, herbal, smoke, citrus, acid, spice, fruit, floral)
- **Blend+Struct slider**: 21 steps with ‹/› step buttons; transitions animate over ~400ms
- **Tooltip**: hover to preview, click to pin; shows nearest neighbors with cosine distances
- **Resizable sidebar**: drag handle (180–520px), orange highlight on active drag
- **Force-simulation labels**: non-overlapping text with leader lines; runs on each redraw
- **Zoom & pan**: standard D3 zoom behavior

---

## Part II: Observations

### How Our Clusters Compare to Human Taxonomies

The most influential human framework for organizing cocktails is the **Cocktail Codex** (Morgenthaler/Teague/DeGroff, 2016), which identifies six "root" cocktails that generate the rest of the canon through systematic substitution:

| Codex Root | Core structure |
|---|---|
| Old Fashioned | spirit + sweetener + bitters |
| Martini | spirit + aromatized wine ± modifier |
| Daiquiri | spirit + citrus + sweetener |
| Sidecar | spirit + citrus + sweetener + liqueur (equal-parts) |
| Highball | spirit + large-format mixer (carbonated) |
| Flip | spirit + fat/egg/dairy |

The Codex taxonomy is fundamentally **structural** — it's about ratios and roles, not flavors. A Negroni is a Martini because it's spirit + aromatized wine + modifier in roughly 1:1:1, regardless of whether it tastes anything like a gin Martini.

#### What BLEND captures well
The flavor-only strategy organizes drinks by **what they actually taste like**. It does a good job of pulling together drinks that are genuinely similar to drink:

- Daiquiri, Mojito, Caipirinha, Hemingway Daiquiri, and Pisco Sour form a tight cluster — all refreshing, lime-forward, lightly sweet rum/pisco drinks
- Manhattan, Perfect Manhattan, Remember the Maine, Greenpoint, Little Italy, Red Hook sit together — all rye-forward, sweet-vermouth-bittersweet stirred drinks
- Martini variants (Martini, Martini Olive, Vesper, Fifty-Fifty, Casino, Tuxedo) cluster tightly

What it misses: The Codex "Martini family" (which includes Negronis, Manhattans, and Adonis) gets broken apart by flavor — Negroni ends up near Americano and La Rosita (correct by taste) rather than near Martini (correct by structure).

#### What ROLE-SLOT captures well
This strategy most closely approximates the Codex taxonomy. The Negroni, Boulevardier, Old Pal, Mezcal Negroni, and White Negroni all land together because they share the same slot grammar (spirit base + aromatized wine modifier + bitter/aperitivo accent), regardless of whether the base is gin, bourbon, or mezcal, or whether the accent is campari or suze.

Manhattan and its variants (Rob Roy, Black Manhattan, Perfect Manhattan, Dry Manhattan) cluster together, as do the daiquiri-template sours (Daiquiri, Mojito, Gimlet, Caipirinha, Rum Sour, Mezcal Sour, Tequila Sour, Whiskey Sour, Gold Rush, Bees Knees) — drinks that are structurally base + citrus + sweetener in roughly 4:1.5:1 ratios.

The biggest drift from Codex: drinks with unusual slot-filling. The Martinez (old tom gin + sweet vermouth + maraschino + bitters) clusters closer to the Negroni-family than to the Martini-family in role-slot view, because maraschino as an `accent` makes its 4-slot grammar look more like a Negroni than a 2-ingredient stirred drink.

#### What PERCEPTUAL captures
This strategy produces the most intuitive groupings for an experienced drinker. It's the only strategy where Aperol Spritz clusters near Adonis and El Presidente — drinks that share a light, slightly bitter, gently wine-forward character — rather than near French 75 (which shares its carbonated structure but has a completely different flavor profile).

The perceptual view also shows the sharpest gin-versus-whiskey-versus-rum separations, because the flavor profiles of base spirits dominate after up-weighting intense components.

---

### What Is Working

**BLEND** — Very reliable for "what does this drink taste like" questions. The nearest-neighbor lists read like a competent bartender's recommendations: "if you like X, try Y." Daiquiri → Mojito → Caipirinha is a perfect progression. Manhattan → Rob Roy → Black Manhattan works beautifully.

**ROLE-SLOT** — Best at recovering structural families. Negroni variants, Manhattan variants, and sour-template drinks all cluster correctly. The Americano fix (moving campari from `base` to `accent`) demonstrates the leverage this strategy has: a single role reassignment collapsed a 3+ unit distance to 0.87.

**PERCEPTUAL** — Best for "bar navigation" — finding drinks a guest might actually want to try next. The nearest-neighbor lists tend to be the most semantically useful of the three stable strategies.

**AlignedUMAP for BLEND+STRUCT** — The slider now gives a genuine continuous deformation of the manifold rather than discontinuous jumps. Structure-heavy view (α ≈ 0) groups by how a drink is built; flavor-heavy view (α ≈ 1) groups by taste. Watching individual drinks travel as you move the slider reveals which cocktails are "accidents of flavor" (same taste, different structure) vs. "structural cousins" (same template, different flavor).

---

### Further work needed

**BLEND+STRUCT in the middle (α ≈ 0.5)** — The clusters are meaningful at both endpoints but somewhat weaker at the midpoint. This is somewhat fundamental: the "average" of a structural signal and a flavor signal doesn't necessarily produce a coherent single signal. Silhouette score drops from ~0.81 (endpoints) to ~0.53 (midpoint). The topology is stable (thanks to AlignedUMAP), but the clusters are genuinely less pronounced at α=0.5 — this may be irreducible.

**ABV / proof as a dimension** — Currently absent from the flavor profiles entirely. This is a significant missing axis. In the perceptual view, the Martinez (high-proof old tom gin + sweet vermouth) clusters near the Negroni, which is fine — but it also ends up near the Tequila Old Fashioned, which a drinker would find surprising. Both are stirred-spirit-forward drinks, but one is spirit+vermouth and the other is spirit+sweetener+bitters — structurally completely different families. ABV and dilution are not captured by any strategy.

**Seasoning ingredients (bitters, absinthe rinses)** — Modeled at a fixed low weight (0.02 × total volume) with `ml=None` in the data. This is a reasonable proxy but inaccurate: the aromatic intensity of 2 dashes of Peychaud's bitters in a Sazerac is not the same as 2 dashes of angostura in a Manhattan. Bitters express differently depending on dilution and base spirit chemistry.

**Equal-parts cocktails** — The Last Word, Final Ward, Naked & Famous, and Paper Plane (all equal-parts templates) share a structural trait that none of our strategies explicitly capture: every slot has equal weight. They end up distributed across different clusters depending on their flavor profiles, when a bartender would recognize them as the same structural template. A 4-way equal-parts slot as a distinct strategy dimension could be interesting. 

---

### Outliers and Oddities

**Trinidad Sour** — A genuine outlier in every strategy. It's built like a sour (citrus + sweetener) but with 45ml of Angostura bitters as the primary spirit. Nothing else in the dataset has angostura as a base, so it has no close neighbors regardless of strategy. In role-slot view its nearest neighbors are Army Navy (orgeat-based gin sour), Industry Sour (fernet+chartreuse sour), and Saturn (gin + falernum + orgeat) — all drinks with unusual, intense bittering or herbal-forward modifiers. That's actually a defensible cluster.

**Aperol Spritz in ROLE-SLOT** — Its closest neighbor is the Americano, which is correct (both are sweet vermouth + campari-family + carbonated), but after that it jumps to Chartreuse Swizzle and Jersey Cocktail. The issue is that Aperol Spritz has no spirit base — it's the only drink in the dataset where the `base` slot is filled by an aperitivo (Aperol) rather than a distilled spirit. This makes it structurally unlike anything else.

**Penicillin** — Clusters correctly with whiskey sours in role-slot (base + citrus + sweetener + accent), but the peated scotch float (7.5ml islay scotch as `accent`) is not well-captured by the current approach. The accent is the entire personality of the drink, but it represents only ~7% of volume, so it's numerically minor. A perception-weighted approach would help here.

**Vesper / Tuxedo / Brooklyn** — These three show the largest displacement between BLEND and ROLE-SLOT strategies (normalized drift of 3.5, 3.4, 3.4 respectively). The reason: all three have **dry vermouth as the modifier** (rather than the more common sweet vermouth), which in role-slot creates a slot-vector that's quite different from most other stirred Martini-family drinks. But in flavor-space they're indistinguishable from other gin/rye + vermouth + accent drinks. The dry vermouth acts as a structural differentiator that isn't a strong flavor differentiator.

**Martinez** — In perceptual view, sometimes ends up next to the Negroni, which is reasonable, though not always (both are spirit-forward, but the intense bitterness of the Negroni isn't present in the Martinez). But it also lands near the Tequila Old Fashioned, which is less intuitive. The connecting thread is that the Martinez's maraschino contributes a mild sweetness and nuttiness that reads similarly to agave sweetener — neither is strongly bitter or citrus-forward. This might indicate a missing **"sweetener character"** dimension that would distinguish cherry-forward sweetness from agave/cane sweetness.

**El Presidente** — Consistently isolated in role-slot (nearest neighbor distance 0.287, the third-highest in the strategy). It's a white rum + dry vermouth + curaçao + grenadine build — the only drink with dry vermouth as modifier, curaçao as accent, and a sweetener in a stirred template. Its flavor profile and structural grammar are genuinely unusual. This is correct behavior, not a bug.

---

### Cluster Migrations: How Tau Shapes the Map

We introduced the tau (τ) parameter in the softmax perceptual strategy to allow us to experiment with how different ingredient weighting schemes affect clustering. Changing values of τ create a continuous spectrum from...
- **intensity-dominated** (low τ), where a small amount of an intense ingredient, like chartreuse or mescal, can dominate the cluster assignment to
- **volume-dominated** (high τ), where the impact of an ingredient is more proportional to its volume

As you slide from τ=0.1 to τ=316, cocktails migrate between clusters in revealing ways:

#### The Most Mobile Cocktails

These drinks visit 8 different clusters across the tau range, indicating they occupy ambiguous positions in cocktail space:

- **Aviation** (gin/lemon/maraschino) — The maraschino liqueur dominates at low τ, grouping it with other maraschino drinks. At high τ, the gin volume takes over, moving it to gin sour clusters.

- **Boulevardier** (bourbon/vermouth/Campari) — At low τ, Campari's intensity places it with Negronis and Americanos. At high τ, bourbon volume moves it to whiskey clusters.

- **Champs-Élysées** (cognac/lemon/yellow Chartreuse) — Yellow Chartreuse dominates at low τ (intense herbal cluster). At high τ, cognac and lemon volumes place it with brandy sours.

- **Division Bell** (mezcal/Aperol/maraschino) — Three intense ingredients pull it different directions. At low τ it clusters by whichever intensity wins locally; at high τ mezcal's volume dominates.

#### Key Tau Breakpoints

**τ ≈ 0.1 (Maximum Intensity)**
- Clusters form around single intense ingredients: Campari cluster, green Chartreuse cluster, Fernet cluster
- Base spirits nearly irrelevant — a gin drink with Campari groups with whiskey drinks with Campari
- Martinis surprisingly group with Alaska (gin/yellow Chartreuse) due to vermouth's herbal intensity

**τ ≈ 2-3 (Balanced)**
- Most semantically coherent clusters emerge
- Intensity still matters but volume provides context
- Paper Plane finally groups with other equal-parts drinks rather than just "Aperol drinks"
- Penicillin's smoky Islay float still pulls it toward mezcal drinks

**τ ≈ 20-30 (Volume-Weighted)**
- Base spirit becomes primary organizing principle
- Whiskey drinks group together regardless of modifiers
- Gin drinks separate into London Dry vs. Old Tom clusters
- Citrus vs. non-citrus becomes a major axis

**τ > 100 (Approaching Pure Volume)**
- Essentially converges to the BLEND strategy
- Large-volume mixers dominate: Collins drinks group together
- Spritz-style drinks (prosecco-based) form their own cluster
- High-proof stirred drinks separate from lower-ABV shaken drinks

#### Drinks That Reveal Strategy Limitations

Several cocktails' migrations expose what each strategy captures or misses:

**Americano** — Changes clusters 7 times. At low τ, Campari dominates (bitter cluster). At high τ, soda water volume makes it group with spritzes and Collins drinks. The "correct" placement depends on whether you think of it as "a Negroni without gin" or "a bitter spritz."

**Corpse Reviver #2** — Equal parts gin/lemon/Cointreau/Lillet with absinthe rinse. At low τ, the absinthe rinse has outsized influence. At mid τ, it's an equal-parts drink. At high τ, it's just another gin sour. Each view is defensible.

**Chartreuse Swizzle** — At low τ, green Chartreuse's intensity completely dominates, grouping it with Last Word and Bijou. At high τ, the pineapple and lime volumes make it a rum-adjacent tropical drink. Both are true.

#### The Stable Cores

Some drinks barely move across the entire tau range, indicating unambiguous positions:

- **Martini variations** — Always cluster together (gin + vermouth is distinctive at any τ)
- **Manhattan family** — Whiskey + vermouth maintains coherence
- **Classic Daiquiri/Gimlet/Margarita** — Simple sours stay together
- **Negroni** — The equal balance of gin/vermouth/Campari keeps it stable

These stable clusters represent the "canonical" drinks that define their categories, while the mobile cocktails occupy the interesting boundaries between flavor families.

---

### Data Sensitivity: Would Different Profiles Change Things?

Yes, substantially. A few specific cases:

**Prosecco** — Modeled as `grain: 0.4, nutty: 0.3, fruit/citrus/floral/acid: 0.1 each`. This is a fairly neutral, slightly wine-like profile. If we had modeled prosecco as more strongly `fruit: 0.4, floral: 0.3` (a riper, more aromatic style), the French 75 and Aperol Spritz would drift toward the fruity-floral cluster rather than the neutral-fizz cluster. The "right" answer depends on the specific prosecco being used.

**Campari** — The most leveraged ingredient in the dataset: it appears in Negroni, Boulevardier, Old Pal, Mezcal Negroni, La Rosita, Americano, Jungle Bird, and Division Bell. Its profile is heavily `bitter` and `citrus`. Increasing its `herbal` component would pull all those drinks closer to the Chartreuse/Benedictine family. The current profile produces accurate clustering for the Negroni family, so it seems well-calibrated.

**Angostura Bitters** — Currently not profiled as intensely as its actual character warrants. Angostura has strong clove, allspice, and cinnamon character (`spice: 0.9, herbal: 0.7`) but because it's modeled at low fixed weight (0.02), its influence is minor. If bitters were modeled by aromatic concentration rather than volume, the Old Fashioned, Manhattan, and Rob Roy would all drift toward the spiced/herbal quadrant of the flavor space.

**A Codex-color overlay** — Adding a color variable for Codex family membership (Old Fashioned / Martini / Daiquiri / Sidecar / Highball / Flip) would be the most useful new color dimension for comparing our machine-derived clusters against human intuition. The ROLE-SLOT strategy should show the strongest alignment with Codex families; BLEND should show the strongest divergence (particularly splitting the Martini family into multiple flavor-based groups).

---

### What Dimensions Are Humans Using?

Based on how experts talk about cocktail families, the useful dimensions appear to be, roughly in order of discriminating power:

1. **Base spirit category** (gin / whiskey / rum / tequila / brandy / wine-based / liqueur-forward) — this is the first question a bartender asks
2. **Structural template** (spirit-forward stirred / sour / highball / equal-parts) — Codex-style
3. **Sweetener type** (sugar syrup / honey / liqueur / none / amaro) — affects perceived weight
4. **Bitterness source** (campari / amaro / dry vermouth / none) — clusters the bitter-aperitivo family
5. **Citrus presence** (yes/no, and lime vs. lemon) — divides sours from stirred drinks
6. **ABV / dilution** (high-proof, room-temp spirit-forward vs. diluted, chilled, extended) — entirely absent from current model

The current strategies capture (1) weakly (via ingredient flavor profiles), (2) strongly via role-slot, (3) weakly (sweeteners are mostly neutral in flavor profile), (4) moderately (campari and amaro bitterness is encoded), (5) strongly (citrus slot is explicit), and (6) not at all.

The most impactful missing addition would be **ABV as an explicit feature dimension**, since proof level is one of the first things both experienced drinkers and bartenders use to navigate preference.

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install umap-learn numpy scipy openpyxl scikit-learn

# Build embeddings
python scripts/build_embeddings.py

# Serve viz locally
python -m http.server 8000
# → open http://localhost:8000/viz/index.html
```

## Deployment

This project supports two deployment strategies:

### Option 1: Static Hosting (DreamHost, GitHub Pages, etc.)

The `public/` directory contains a completely static version ready for deployment:

```bash
# Test locally
cd public && python3 -m http.server 8888
# → open http://localhost:8888

# Deploy to DreamHost via rsync
./deploy.sh <username> cocktail-cartography.com

# Or manually upload the public/ directory contents via FTP
```

See [DEPLOY_DREAMHOST.md](DEPLOY_DREAMHOST.md) for detailed DreamHost deployment instructions and [DOMAIN_SETUP.md](DOMAIN_SETUP.md) for domain configuration.

### Option 2: Container Deployment (Fly.io, Heroku, etc.)

The project includes Docker and Fly.io configuration for container-based deployment:

```bash
# Deploy to Fly.io
fly deploy

# Point custom domain to Fly.io app
fly certs add cocktail-cartography.com
```

The containerized version runs a minimal Express server for compatibility with platform-as-a-service providers.

## Files

```
data/
  ingredients.xlsx    ← source of truth for flavor profiles
  ingredients.csv     ← exported from xlsx
  recipes.json        ← 102 cocktail recipes with roles + volumes
  taxonomy.json       ← ingredient hierarchy for color coding
  embeddings.json     ← pre-built UMAP output (102 cocktails × 4 strategies)
scripts/
  build_embeddings.py ← builds embeddings.json from the data files
  export_ingredients.py ← exports xlsx → csv
viz/
  index.html          ← self-contained D3 v7 visualization
loaders.py            ← shared data loading utilities
utils.py              ← shared flavor vector utilities
```
