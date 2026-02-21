# Cocktail Cartography

An interactive clustering visualization of 102 classic cocktails, showing you how different ways of thinking about what makes cocktails similar produces different — and sometimes surprising — groupings.

The viz runs locally: `python -m http.server 8000` → [http://localhost:8000/viz/index.html](http://localhost:8000/viz/index.html)

---

## What This Is

This project takes 102 classic cocktails and organizes them into visual clusters based on four different theories of similarity. You can switch between these views and watch drinks move around as the definition of "similar" changes.

The dataset includes everything from workhorses like Daiquiri (60ml white rum / 22.5ml lime / 15ml simple) and Manhattan (60ml rye / 30ml sweet vermouth / bitters) to oddities like Trinidad Sour (45ml Angostura as the base spirit) and equal-parts templates like Last Word and Paper Plane.

---

## The Four Ways of Grouping

### BLEND: Pure Flavor Profile
Groups drinks by what they actually taste like, regardless of how they're built. Each ingredient has a flavor profile across 15 dimensions (sweet, bitter, saline, acid, herbal, spice, citrus, floral, fruit, smoke, oak, grain, vegetal, nutty, anise), and the drink's overall flavor is just the weighted average based on volume.

**What clusters well:**
- Daiquiri, Mojito, Caipirinha, Hemingway Daiquiri, Pisco Sour — refreshing lime-forward drinks
- Manhattan, Perfect Manhattan, Remember the Maine, Greenpoint, Little Italy — rye + sweet vermouth stirred drinks
- All the Martini variations stay tight together

**What splits apart:**
- Negroni and Manhattan don't cluster together, even though they're both "spirit + aromatized wine + modifier" structurally — they just taste completely different

### BLEND+STRUCT: Flavor With a Structure Slider
This adds structural information (stirred vs. shaken, served up vs. on ice, ingredient count) and lets you blend it with flavor using a slider. At one extreme it's pure structure, at the other it's pure flavor, and you can watch the map morph smoothly in between.

The interesting action is watching individual drinks migrate. A Boulevardier starts near Negronis (same structure) and drifts toward whiskey Old Fashioneds (similar flavor) as you slide toward the flavor end.

The slider implementation uses a technique called AlignedUMAP — basically it keeps 21 different snapshots (from 0% structure to 100% structure in 5% increments) from jumping around discontinuously. Without this, moving the slider one notch could make half the drinks teleport across the map.

**Worth watching:**
- Americano's journey — it shares Campari + vermouth with Negroni but has soda water instead of gin, so it migrates between bitter aperitivo clusters and fizzy spritz territory
- Martinez (old tom gin / sweet vermouth / maraschino / bitters) moves between Negroni-land and Martini-land depending on whether you weight structure or flavor

### ROLE-SLOT: Grammar Over Flavor
Treats each drink as having up to four functional slots: base spirit, modifying ingredients (vermouth/sweetener), citrus, and accent. Each slot gets its own 15-dimensional flavor sub-vector. Two drinks can taste similar but cluster far apart if the same flavors come from different structural positions.

The Negroni / Americano story is instructive here: when we originally coded Americano with Campari as the `base` (since there's no spirit), it landed far from Negroni. Changing Campari to `accent` collapsed them to nearly the same point — because now they have the same grammar: sweet vermouth base + Campari accent + something else (gin vs. soda).

**What this captures:**
- Negroni, Boulevardier, Old Pal, Mezcal Negroni, White Negroni — all equal-parts "base + modifier + accent" templates
- All the sours (Daiquiri, Whiskey Sour, Margarita, etc.) cluster together because they're all "base + citrus + sweetener"
- Manhattan variants (Rob Roy with scotch, Black Manhattan with Averna instead of vermouth) stay together

**What breaks:**
- Drinks with unusual slot-filling. Martinez has maraschino as an accent, which makes its grammar look more like Negroni than like Martini, even though bartenders think of it as a proto-Martini.

### PERCEPTUAL: Intensity-Weighted Flavor
Like BLEND, but amplifies ingredients that punch above their weight. A Penicillin has 60ml blended scotch and 7.5ml Islay scotch as a float — the Islay is only ~11% by volume but it's the entire personality of the drink. Same with Fernet in a Hanky Panky, green Chartreuse in a Bijou, or the absinthe rinse in a Sazerac.

The model takes the strongest value each ingredient contributes to each flavor dimension, then blends that with the volume-weighted average (40% max / 60% volume-weighted).

**What this gets right:**
- Penicillin clusters closer to smoky mezcal drinks than to regular scotch sours
- Hanky Panky (gin + vermouth + Fernet) clusters near other Fernet-forward drinks, not near regular Martini variations
- Aperol Spritz ends up near Adonis and El Presidente (light, wine-forward, gently bitter) rather than near French 75 (which shares the fizz but tastes completely different)

**What it can't fully capture:**
- A 2ml absinthe rinse vs. 22ml of absinthe as a full pour — the model up-weights both equally because they both have high herbal intensity, but it doesn't know one is a rinse and one is a base ingredient

---

## Interesting Findings

### Stable Cores
Some drinks barely move across all four strategies — they're unambiguous classics that define their categories:
- Martini variations (Martini, Fifty-Fifty, Vesper) always cluster together
- The Manhattan family (Manhattan, Rob Roy, Perfect Manhattan) stays coherent
- Classic simple sours (Daiquiri, Gimlet, Margarita) cluster reliably

### The Travelers
These drinks visit wildly different neighborhoods depending on strategy:

**Boulevardier** (bourbon / sweet vermouth / Campari) — In structure view it's with Negronis. In flavor view it drifts toward whiskey-vermouth drinks. It occupies the boundary between bitter aperitivo territory and Manhattan-land.

**Aviation** (gin / lemon / maraschino / crème de violette) — The maraschino dominates in perceptual view, grouping it with Last Word and Hemingway Daiquiri. In volume-weighted view, the gin takes over and it becomes a gin sour.

**Corpse Reviver #2** (equal parts gin / lemon / Cointreau / Lillet + absinthe rinse) — In perceptual view the absinthe rinse has outsized influence. In role-slot view it's an equal-parts drink. In pure flavor view it's just a gin sour. Each is defensible.

### Genuine Outliers

**Trinidad Sour** — Absolutely isolated in every strategy. It's a sour template but with 45ml Angostura bitters as the base spirit. Nothing else in the canon does this.

**El Presidente** (white rum / dry vermouth / curaçao / grenadine) — The only drink with dry vermouth as modifier, curaçao as accent, and grenadine as sweetener in a stirred build. Its grammar is genuinely unique.

**Aperol Spritz** in role-slot view — It has Aperol as the base (not a spirit), which makes it structurally unlike anything else in the dataset.

### Base Spirit Drift
One of the most visible axes across all strategies is base spirit, even though we never explicitly told the model "gin vs. whiskey matters." The flavor profiles naturally separate:
- Gin clusters (juniper, floral, herbal)
- Whiskey clusters (oak, grain, spice)
- Rum clusters (fruit, lighter body)
- Agave clusters (vegetal, earthy)

But the *boundaries* between these clusters change. In BLEND, an Aviation can drift toward whiskey territory if the maraschino and violette pull it away from juniper. In PERCEPTUAL, anything with intense smoky mezcal or Islay scotch groups together regardless of the base spirit category.

---

## What's Missing

**ABV / Proof** — Entirely absent from the current model. A Vesper (high-proof gin + vodka + Lillet) and a Sherry Cobbler (low-ABV sherry + juice) could theoretically cluster together if their flavor profiles matched, but no bartender would recommend them as substitutes. Strength is one of the first filters people use.

**Dilution & Serving Temperature** — A stirred-and-served-up Martini vs. a shaken-and-served-up Vesper vs. an on-ice Negroni all have different dilution and temperature profiles that dramatically affect perception. The model treats "served up" and "on ice" as binary structural flags but doesn't capture the sensory impact.

**Bitters as Aromatic Intensity** — Angostura, Peychaud's, and orange bitters are modeled at a fixed low weight, but 2 dashes of Peychaud's in a Sazerac express completely differently than 2 dashes of Angostura in a Manhattan. They're not interchangeable.

**Sweetener Character** — The model knows maraschino is sweet, but it doesn't distinguish maraschino's cherry/almond character from honey's floral character from agave's vegetal character. A bartender absolutely does.

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

## Using the Viz

**Shapes:** ▽ = served up, ■ = on ice, ● = either
**Color options:** base spirit, cocktail family, served, dominant flavor, or individual flavor channels (sweet, bitter, herbal, smoke, citrus, acid, spice, fruit, floral)
**Tooltips:** hover to preview, click to pin; shows the 5 nearest neighbors by true high-dimensional distance, not just visual proximity
**Blend+Struct slider:** use ‹ / › to step through, or drag; transitions animate smoothly

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
  ingredients.xlsx    ← flavor profiles (source of truth)
  ingredients.csv     ← exported from xlsx
  recipes.json        ← 102 recipes with roles + volumes + methods
  taxonomy.json       ← ingredient hierarchy
  embeddings.json     ← pre-built UMAP output
scripts/
  build_embeddings.py ← builds embeddings
  export_ingredients.py ← exports xlsx → csv
viz/
  index.html          ← D3 v7 visualization
```
