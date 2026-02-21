# Cocktail Cartography

An interactive map of 102 classic cocktails that shows you which drinks are similar to each other — and lets you explore *why* they're similar by switching between different ways of thinking about cocktails.

---

## Why this exists

One thing I love about cocktails is their variety. So it took me a lot of years and lot "I ordered this so I guess I'll drink it..." moments to figure out what I actually enjoy. Every now and then, you meet a great bartender who knows the territory and happens to have the time to really understand what you might like (Cecily at ABV 10 years ago, stands out in mind). But if you're not lucky enough to run into your own Cecily, and especially if you don't exactly speak the local language of spirits yet, this page is here to help you learn the territory, and hopefully find your next favorite by starting with the familiar, and moving into similar territory.

But then I went down a rabbit hole trying to figure out how to define "similar." I started quantifying ingredients across taste components, and that was straightforward, if painstaking. I wound up with 15 dimensions for each ingredient (sweet, bitter, saline, acid, herbal, spice, citrus, floral, fruit, smoke, oak, grain, vegetal, nutty, anise). 

Then you have to make a cocktail, and that gets complicated. A negroni and a Martinez have very similar recipes (gin, sweet vermouth, and then Campari or maraschino liqueur, respectively), but the Campari adds a punch of bitterness that makes them quite different. A margarita and a gin gimlet come from different worlds, but they're both citrus-forward cocktails with a sweet and sour balance. How do we map that out? 

In the end, I decided... not to decide. Instead, I built this tool to explore the territory, and see how different ways of thinking about cocktails can lead to different insights, and hopefully find some new favorites.


---

## The Four Different Views

Here's the interesting part: the answer changes depending on whether you want something that *tastes* similar, or something that's *made* in a similar way.

You can switch between four different ways of grouping the cocktails. Each one tells you something different about what makes drinks similar.

### "Flavor" View
Groups drinks by what they actually taste like, ignoring how they're made.

**What ends up together:**
- Daiquiri, Mojito (which is basically a Daiquiri with mint), and Caipirinha (which uses cachaça — Brazilian sugarcane spirit — instead of rum) all cluster together because they're refreshing, lime-forward, lightly sweet drinks
- Manhattan and Rob Roy (which is the same drink but with scotch instead of rye whiskey) stay next to each other
- All the Martini variations stay grouped

**What splits apart:**
- Negroni and Manhattan don't end up near each other, even though they're both made the same way (spirit + vermouth + something else, stirred and served). They just taste completely different — one is bitter and herbaceous, the other is sweet and whiskey-forward.

### "Flavor + Structure" View (with a slider)
This view has a slider that lets you blend between "how it's made" and "how it tastes." You can watch drinks move around the map as you change what matters.

At one end of the slider, drinks group by:
- Stirred vs. shaken vs. built (poured directly in the glass)
- Served up (in a cocktail glass, no ice) vs. on ice
- Number of ingredients

At the other end, it's pure flavor. In between, it's a mix of both.

**Worth watching:**
- The Boulevardier (whiskey, sweet vermouth, Campari — basically a Negroni made with bourbon instead of gin) starts near other Negroni-style drinks and drifts toward whiskey drinks as you move the slider toward "flavor"
- Aperol Spritz wanders between bitter Italian aperitivo drinks and light fizzy drinks depending on whether you weight structure or taste

### "Grammar" View
This one treats cocktails like sentences with a specific structure. Each drink has up to four "slots":
1. **Base spirit** (gin, whiskey, rum, tequila, etc.)
2. **Modifying ingredients** (vermouth, liqueurs)
3. **Citrus** (lemon, lime, grapefruit)
4. **Accent** (the thing that gives it personality — Campari in a Negroni, green Chartreuse in a Last Word)

Two drinks can taste similar but land far apart if the same flavors come from different positions in the recipe.

**Example:** The Negroni and Americano both use Campari and sweet vermouth, but Negroni has gin as the base and Americano has soda water. In this view, they cluster together because Campari plays the same role in both (the "accent" that defines the drink). But in the flavor view, they can drift apart because one is spirit-forward and one is light and fizzy.

**What this captures:**
- All the Negroni variations (Boulevardier with bourbon, White Negroni with Suze instead of Campari, Mezcal Negroni, etc.) cluster together because they're all "base spirit + vermouth + bitter accent" in equal parts
- All the sours (Daiquiri, Whiskey Sour, Margarita, etc.) group together because they're all "base spirit + citrus + sweetener"

### "Intensity" View
Like the flavor view, but it gives extra weight to ingredients that "punch above their weight" — things that are super intense even in small amounts.

**Example:** A Penicillin has 2 ounces of regular scotch and just ¼ ounce of Islay scotch (the super smoky kind) floated on top. By volume, the Islay is only about 11% of the drink, but it completely defines what the drink tastes like. This view recognizes that and groups the Penicillin with other smoky drinks.

Same with:
- Hanky Panky (gin + vermouth + a tiny bit of Fernet Branca, which is an intensely bitter/minty Italian liqueur) clusters with other Fernet drinks rather than regular Martinis
- Sazerac (whiskey + sugar + bitters, with an absinthe rinse — just a few drops coating the glass) gets pulled toward anise-flavored drinks because that absinthe hits hard
- Bijou (gin + vermouth + green Chartreuse, an intensely herbal liqueur) clusters with other Chartreuse drinks

**What it can't do perfectly:**
- It can't tell the difference between "a few drops of absinthe as a rinse" and "a full ounce of absinthe as a main ingredient." Both get up-weighted for intensity, but obviously one is way more absinthe-forward than the other.

---

## Interesting Patterns You Might Notice

### Drinks That Stay Together No Matter What
Some cocktails are just... unambiguous. They cluster the same way in all four views:
- The Martini family (Martini, Dry Martini, Fifty-Fifty Martini) always groups together
- The Manhattan family (Manhattan, Rob Roy, Perfect Manhattan) stays coherent
- Simple sours (Daiquiri, Gimlet, Margarita) always cluster

These are the "classics" that define their categories.

### Drinks That Travel
These cocktails move to completely different neighborhoods depending on which view you're using:

**Boulevardier** (bourbon + sweet vermouth + Campari)
- In "grammar" view: with Negronis (same structure)
- In "flavor" view: drifts toward Manhattan-style whiskey drinks
- It's a boundary-dweller between bitter Italian aperitivo territory and American whiskey land

**Aviation** (gin + lemon + maraschino cherry liqueur + crème de violette)
- In "intensity" view: clusters with other maraschino-heavy drinks
- In "flavor" view: the gin dominates and it becomes just another gin sour

**Corpse Reviver #2** (gin + lemon + Cointreau + Lillet + absinthe rinse)
- In "intensity" view: the absinthe rinse pulls it toward licorice/anise drinks
- In "grammar" view: it's an equal-parts drink (all four liquid ingredients are the same amount)
- In "flavor" view: it's basically a gin sour

Each interpretation is defensible — these drinks genuinely occupy the interesting spaces *between* categories.

### The Genuine Weirdos

**Trinidad Sour** — This drink is completely isolated in every view. Instead of using a normal base spirit, it uses 1.5 ounces of Angostura bitters (yes, the stuff you usually add a few drops of) as the main ingredient, with just ½ ounce of whiskey and some orgeat (almond syrup) and lemon. Nothing else in the cocktail canon does this.

**El Presidente** (white rum + dry vermouth + curaçao + grenadine) — Structurally unique. It's the only drink in the dataset that combines these specific ingredients in this specific way. Tastes great, just... different.

---

## What This Doesn't Tell You (But Maybe Should)

**How strong the drink is**
A Martini is basically pure alcohol (gin + a little vermouth, maybe 30% alcohol after you stir it with ice and dilute it a bit). A Sherry Cobbler is mostly fortified wine and juice, maybe 8% alcohol. The map doesn't know this, so it could theoretically group them together if their flavors matched. But obviously if you're looking for "something like a Martini," you probably care about the strength.

**How cold and diluted it is**
Shaken drinks are colder and more diluted than stirred drinks (more ice contact, more agitation). Built drinks (poured directly over ice) keep diluting as you drink them. This completely changes how a drink feels in your mouth, but the map doesn't capture it.

**Sweetener personality**
The map knows maraschino cherry liqueur is sweet, but it doesn't distinguish:
- Cherry/almond sweetness (maraschino)
- Floral honey sweetness (honey syrup)
- Vegetal agave sweetness (agave syrup)
- Pomegranate sweetness (grenadine)

These taste really different, but the model just sees "sweet."

---

## Using the Map

**Shapes:**
- Triangle pointing down (▽) = served "up" in a cocktail glass
- Square (■) = served on ice
- Circle (●) = can be served either way

**Colors:**
You can color the dots by:
- Base spirit (gin, whiskey, rum, tequila, etc.)
- Dominant flavor (sweet, bitter, citrus, smoky, etc.)
- Individual flavors (just the sweet ones, just the bitter ones, etc.)

**Clicking on a drink:**
Shows you the 5 most similar drinks based on the true recipe similarity (not just what's close on the map, because the map is a flattened approximation).

**The slider (Flavor + Structure view only):**
Use the ‹ / › buttons to step through, or drag the slider. You'll see the dots animate smoothly to new positions as the definition of "similar" changes.

---

## A Few Cocktails You Might Recognize

In case you want to orient yourself on the map, here are some classics and how they're made:

**Margarita:** 2 oz tequila, 1 oz lime juice, 1 oz Cointreau (orange liqueur). Shaken, served up or on ice with salt rim.

**Manhattan:** 2 oz rye whiskey, 1 oz sweet vermouth, bitters. Stirred, served up with a cherry.

**Martini:** 2.5 oz gin, 0.5 oz dry vermouth, bitters. Stirred, served up with lemon twist.

**Daiquiri:** 2 oz white rum, 0.75 oz lime juice, 0.5 oz simple syrup. Shaken, served up.

**Negroni:** 1 oz gin, 1 oz sweet vermouth, 1 oz Campari. Stirred, served on ice with orange twist. (Note: everything is equal parts — this is key to the drink.)

**Old Fashioned:** 2 oz bourbon, ¼ oz simple syrup (or a sugar cube), bitters. Built in the glass over ice, orange twist.

**Aperol Spritz:** 2 oz Aperol, 3 oz prosecco, splash of soda water. Built in glass over ice, orange slice.

**Whiskey Sour:** 2 oz bourbon, 0.75 oz lemon juice, 0.5 oz simple syrup. Shaken, served up or on ice.

**Gimlet:** 2 oz gin, 0.75 oz lime juice, 0.5 oz simple syrup. Shaken, served up. (Basically a gin Daiquiri.)

**Last Word:** 0.75 oz gin, 0.75 oz lime juice, 0.75 oz maraschino, 0.75 oz green Chartreuse. Equal parts. Shaken, served up. Surprisingly balanced despite the intense Chartreuse.

**Paper Plane:** 0.75 oz bourbon, 0.75 oz lemon juice, 0.75 oz Aperol, 0.75 oz Amaro Nonino. Another equal-parts drink, shaken and served up. Modern classic.

---

## Why This Exists

Cocktail recipes are structured data: you have ingredients, amounts, and methods. But "similarity" is subjective. Do you group by taste? By structure? By the role each ingredient plays?

This project explores that question by showing you all the groupings at once, and letting you switch between them. Sometimes the structure matters more (Negroni and Boulevardier are the "same drink" with different base spirits). Sometimes the flavor matters more (Daiquiri and Mojito taste nearly identical despite different methods).

The map is a tool for curiosity. If you liked a Boulevardier, should you try a Negroni next (same structure, different base spirit) or a Manhattan (same base spirit, different accent)? The answer depends on what you liked about the Boulevardier in the first place.

---

## One More Thing: The Recipes Might Be Different Than Yours

All the recipes come from canonical bartending sources (Cocktail Codex, Death & Co, etc.), but there's always room for interpretation. For example:

- **Negroni:** This map uses equal parts (1 oz each of gin, vermouth, Campari). Some bartenders do 1.25 oz gin to let it lead.
- **Martini:** 5:1 gin to vermouth (2.5 oz gin, 0.5 oz vermouth) is the classic midcentury ratio. Modern "dry" Martinis can be 10:1 or even 15:1.
- **Daiquiri:** The map uses roughly 2:0.75:0.5 (rum:lime:syrup). Some prefer 2:1:1 for a sharper drink.

If a drink doesn't taste like you expect, it's probably not wrong — it's just a different canonical version. The clustering still works because we're comparing recipes to each other, not to your personal preference.

---

## Questions?

This is a side project for exploring how data science applies to something tactile and cultural. If you find it interesting, try the visualization and see which drinks end up near your favorites. You might discover something new.
