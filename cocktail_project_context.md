# Cocktail Clustering Project — Context & Design Decisions

## Project Goal

Build a data structure and clustering system for cocktail recipes that can:
1. Represent recipes as structured data with ingredient roles, proportions, and serving info
2. Compute meaningful similarity between cocktails (flavor-based and structural)
3. Support a fun one-off class titled "Two Recipes, Infinite Cocktails" that goes into two archetypes of cocktails, showing that cocktails fall into families where you swap components to get new drinks

The two archetype families:
- **The Sour** (Last Word archetype): spirit + citrus + sweetener + "the interesting thing." Includes Last Word, Margarita, Daiquiri, Bee's Knees, Paper Plane, Corpse Reviver #2, etc.
- **The Stirred/Spirit-Forward** (Martinez archetype, a.k.a. the Manhattan family): 2 parts base spirit + 1 part vermouth/amaro + "the interesting thing." Includes Martinez, Manhattan, Bijou, Hanky Panky, Vancouver, etc.

## Architecture

Two-layer model:

### Layer 1: Ingredients
Each ingredient has:
- **Category path** in a taxonomy tree (e.g., `["spirit", "whiskey", "bourbon"]`) — encodes "swappability" / kind-of similarity
- **ABV**
- **15-dimensional flavor vector** (0.0–1.0): sweet, bitter, saline, acid, herbal, spice, citrus, floral, fruit, smoke, oak, grain, vegetal, nutty, anise

note: citrus and acid are separate dimensions because they serve different functional roles in cocktails. Orange bitters or peel can provide citrus notes without adding acid, for example. The "acid" dimension was added after the results that were presented/discussed below, and so needs to be incorporated in the next round of comparison. 
Key insight: complexity lives in the ingredient, not the recipe. Sweet vermouth doesn't need to be tagged as "modifier AND bitter AND sweetener" — it just has high values for sweetness AND bitterness in its profile. The clustering algorithm discovers functional similarity.

### Layer 2: Recipes
Each recipe has:
- **method**: stirred | built | shaken (note: Jesse stirs almost everything, shaken is the exception for margaritas) - This dimension might not actually matter, and may actually be a distraction from the real similarities. To experiment with.
- **served**: up | on_ice | either (This DOES matter, as it affects the final drink significantly. Ice in the drink that melts provides a great deal more dilution than a stir before serving)
- **components**: list of `{ingredient, role, ml}` where role is one of: base, modifier, citrus, sweetener, accent, seasoning
- **garnish**: list of garnish ingredient names (garnishes contribute to flavor — olive vs. lemon twist matters)
- **ml is null for seasonings** (bitters) — presence matters, amount doesn't

### Distance Metric
```
distance(A, B) = α * flavor_distance + β * structural_distance
```
- **Flavor distance**: cosine distance of proportion-weighted blended flavor vectors. Seasonings get fixed weight 0.05, garnishes 0.03.
- **Structural distance**: method penalty + serving penalty + euclidean distance of grouped role proportions. "Modifier" and "sweetener" are merged into "modifying" for structural comparison (because sweet vermouth in a Manhattan plays the role that sugar+bitters plays in an Old Fashioned).
    - This is the area that needs the most work. The current implementation is a starting point, but it's not perfect, and appears to be overfitting to the current feedback for a few cocktails. 

## Key Design Decisions

1. **Amounts in ml** (Jesse's preference), not oz
2. **Roles stay simple** — an ingredient occupies one role per recipe. Dual-role complexity is captured by the ingredient's flavor profile, not the recipe structure. (This is an experiment. It may matter more for human legibility than actual distance calculation.)
3. **Gin is just "gin"** unless it's Old Tom (notably sweeter). No need to specify London Dry vs. Plymouth etc. — Jesse uses whatever gin he has.
4. **Amari are "all over the map"** — generalized amaro category with the footnote to experiment. Individual amari (Averna, Cynar, Fernet-Branca, etc.) each get their own flavor profile. Future work: scrape bittersandbottles.com descriptions to build an amaro sub-section.
5. **Category tree + flavor vectors** both matter — the tree captures human-legible "these are the same kind of thing" even when flavor profiles diverge (e.g., two very different amari).
6. **Garnish is a recipe-level list** with flavor profiles on the garnish ingredients themselves. Most drinks will have a single 

## Current State of the Code

`cocktail_data.py` contains:
- `CATEGORY_TREE` — nested dict of the ingredient taxonomy
- `INGREDIENTS` — 30+ ingredients with category paths, ABV, and 14-dim flavor vectors
- `RECIPES` — 24 cocktail recipes with full structural data
- Utility functions: `get_flavor_vector`, `ingredient_flavor_distance`, `category_distance`, `compute_recipe_proportions`, `recipe_flavor_vector`, `recipe_structural_vector`, `recipe_distance`
- Validation script that prints recipe breakdowns, key distance checks, and nearest-neighbor lists

## Validation Results (what's working)

- Ingredient distances are sensible: bourbon↔rye=0.06, bourbon↔gin=0.81, sweet_vermouth↔averna=0.05
- Equal-parts sour family clusters tightly: Last Word, Final Ward, Naked & Famous, Paper Plane, Corpse Reviver #2 all within 0.08
- Spirit-forward family clusters: Martinez↔Vancouver=0.016, Manhattan↔Black Manhattan=0.02
- Bijou↔Tipperary=0.023 (same drink, spirit swap — correct)
- Martini↔Martini(olive)=0.0003 (garnish-only difference — correct)

## Known Issues / Things That Need Tuning

1. **Old Fashioned distance from Manhattan** (0.36). The role grouping helped but the 89% vs 67% base proportion still creates distance. The Old Fashioned is structurally more spirit-forward, which is significant. Need to compare to other distances to see if this is reasonable. (Role grouping seems like a problematic hack, need to compare. These are actually quite different drinks, so it's possible that this is correct, but we need to understand the impact of this grouping on other distances.)
2. **Margarita is somewhat isolated** — it's the only shaken drink, and Cointreau is tagged as "accent" rather than "sweetener." Could relabel or adjust. Shaken may be artifically creating distance on a dimension that doesn't matter ("shaken").
3. **Bee's Knees shows up near Vancouver** (0.16) which seems suspicious. The inclusion of ANY citrus is a significant enough difference that it should create a larger difference. 
4. **Flavor profiles are hand-curated first pass** — need tasting feedback especially on: sweet vermouth (0.5 bitter, 0.6 sweet), green Chartreuse (0.5 sweet, 0.4 bitter, 0.9 herbal), maraschino (0.4 sweet, 0.2 bitter, 0.3 nutty).

## Excluded Ingredients (not buying for class)

Scotch, vodka, cognac, Campari. Will have Chartreuse stand-ins (green and yellow).
Note: cognac IS in the data for Vieux Carré — just won't be available at the class. However, these SHOULD be included in the database for experimentation. We need to see how the different cocktails cluster.

## Future Work

- Run actual clustering (k-means, hierarchical, t-SNE) and visualize
- Scrape bittersandbottles.com for ingredient flavor profiles
- Build class handout / interactive tool from the data
- Potentially build a "suggest a cocktail given what's on the bar" feature


## Research Findings

No existing structured numerical flavor profile database exists for cocktail ingredients. Relevant prior work:
- **Whisky**: Wishart dataset (12 flavor dimensions for 86 scotches), whiskyanalysis.com PCA/cluster analysis
- **Flaviar**: Flavor Spiral visualization (9 prominent flavors per spirit) — visual but not open data
- **Recipe co-occurrence**: Ahn et al. 2011 flavor network, James Gammerman's cocktail PCA on Mr. Boston data
- **Bar Assistant** (github.com/bar-assistant/data): Good recipe schema (JSON, 500+ recipes) with ingredient categories and taste tags (Bright, Bitter, Herbaceous, Citrusy, Fruity, Floral, Savory, Smokey, Spicy, Sweet, Tart) — but no numerical profiles
- **LiquorAlchemy**: 7-dimension flavor map framework (sweet/sour, bitter, salty, creamy↔herbaceous, mineral↔fruity, simple↔complex, light↔heavy) — interesting conceptual framework but no ingredient-level data