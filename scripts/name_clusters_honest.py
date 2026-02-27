#!/usr/bin/env python3
"""Name clusters by what ACTUALLY characterizes them.

Principles:
- Name by what's common to most members (>60%), not minority ingredients
- If something appears in 100% of members, that's the defining feature
- No fluff words (Portfolio, Panorama, Canon, Essence, Heart, Core)
- Honest about diversity — if mixed, say so
- Bartender vocabulary: spirit names, methods, ingredient names
- 2-4 words max
"""
import json
import hashlib
from collections import Counter

with open('viz/clustering_data.json') as f:
    data = json.load(f)

def analyze_cluster(members):
    """Deep analysis of what characterizes a cluster."""
    n = len(members)

    spirits = Counter()
    families = Counter()
    methods = Counter()
    all_ings = Counter()
    served = Counter()

    for m in members:
        r = data['recipes'].get(m, {})
        spirits[r.get('base_spirit', 'unknown')] += 1
        families[r.get('family', 'unknown')] += 1
        methods[r.get('method', 'unknown')] += 1
        served[r.get('served', 'unknown')] += 1
        for ing in r.get('ingredients', []):
            all_ings[ing] += 1

    return {
        'n': n,
        'spirits': spirits,
        'families': families,
        'methods': methods,
        'served': served,
        'ingredients': all_ings,
        'members': members,
    }

def pct(counter, n):
    """Get items with their percentages, sorted by count."""
    return [(k, v, v/n) for k, v in counter.most_common()]

def name_cluster(members):
    """Generate an honest name for a cluster."""
    a = analyze_cluster(members)
    n = a['n']

    spirits_pct = pct(a['spirits'], n)
    families_pct = pct(a['families'], n)
    methods_pct = pct(a['methods'], n)
    ings_pct = pct(a['ingredients'], n)

    top_spirit, top_spirit_n, top_spirit_p = spirits_pct[0]
    top_family, top_family_n, top_family_p = families_pct[0]
    top_method, top_method_n, top_method_p = methods_pct[0]

    # Check for universal ingredients (present in >80% of members)
    universal_ings = [(k, v, p) for k, v, p in ings_pct if p >= 0.80]
    high_ings = [(k, v, p) for k, v, p in ings_pct if p >= 0.60]

    # Spirit name formatting
    spirit_name = {
        'gin': 'Gin', 'whiskey': 'Whiskey', 'rum': 'Rum',
        'agave': 'Agave', 'brandy': 'Brandy', 'vermouth': 'Vermouth',
        'amaro': 'Amaro', 'mixed': 'Mixed-Spirit',
        'bitters': 'Bitters', 'herbal_liqueur': 'Herbal Liqueur',
        'other': 'Mixed-Spirit',
    }

    family_name = {
        'spirit_forward': 'Spirit-Forward',
        'sour': 'Sour',
        'built': 'Built',
    }

    method_name = {
        'stirred': 'Stirred',
        'shaken': 'Shaken',
        'built': 'Built',
    }

    # ─── MICRO CLUSTERS (2-4) ───
    if n <= 4:
        display_names = [data['recipes'][m]['display_name'] for m in sorted(members)]
        if n == 2:
            return f"{display_names[0]} & {display_names[1]}"
        return display_names[0] + " & Kin"

    # ─── SMALL HETEROGENEOUS CLUSTERS (5-7) ───
    # If a small cluster has no strong majority, name by its most recognizable members
    if n <= 7:
        # Check if the cluster is actually heterogeneous
        if top_family_p < 0.70 or top_spirit_p < 0.50:
            # Name by the 2-3 most recognizable cocktails
            well_known = ['old_fashioned', 'manhattan', 'martini', 'negroni', 'margarita',
                         'daiquiri', 'whiskey_sour', 'boulevardier', 'mai_tai', 'mojito',
                         'gimlet', 'sidecar', 'last_word', 'paper_plane', 'sazerac',
                         'old_pal', 'paloma', 'aviation', 'cosmopolitan']
            recognizable = [m for m in members if m in well_known]
            if len(recognizable) >= 2:
                names_list = [data['recipes'][m]['display_name'] for m in recognizable[:2]]
                return f"{names_list[0]} & {names_list[1]} Group"
            # Fall through to normal naming

    # ─── CHECK FOR DEFINING INGREDIENTS ───
    # If one ingredient appears in ALL or nearly all members, that's the identity

    # Angostura bitters in 90%+
    angostura_count = a['ingredients'].get('angostura_bitters', 0)
    if angostura_count / n >= 0.90:
        if top_method_p >= 0.60 and top_method == 'built':
            return "Bitters & Built Spirits"
        if top_spirit_p >= 0.60:
            return f"{spirit_name.get(top_spirit, top_spirit)} Bitters Drinks"
        return "Angostura Bitters Family"

    # Vermouth in 80%+
    vermouth_count = a['ingredients'].get('sweet_vermouth', 0) + a['ingredients'].get('dry_vermouth', 0)
    if vermouth_count / n >= 0.80:
        if top_spirit_p >= 0.50:
            return f"Stirred {spirit_name.get(top_spirit, top_spirit)} & Vermouth"
        return "Vermouth Cocktails"

    # Citrus in 80%+
    citrus_count = sum(a['ingredients'].get(c, 0) for c in
                       ['lemon_juice', 'lime_juice', 'grapefruit_juice', 'orange_juice'])
    citrus_pct = citrus_count / n if n > 0 else 0

    # Campari/Aperol (bitter aperitivo)
    bitter_aperitivo = sum(a['ingredients'].get(c, 0) for c in ['campari', 'aperol'])
    if bitter_aperitivo / n >= 0.60:
        return "Bitter Aperitivo"

    # ─── VERY PURE CLUSTERS ───

    # 90%+ one family AND 70%+ one spirit
    if top_family_p >= 0.90 and top_spirit_p >= 0.70:
        s = spirit_name.get(top_spirit, top_spirit)
        f = family_name.get(top_family, top_family)
        if top_family == 'sour' and top_method_p >= 0.70:
            m = method_name.get(top_method, top_method)
            return f"{m} {s} Sours"
        if top_family == 'spirit_forward':
            if top_method_p >= 0.70:
                m = method_name.get(top_method, top_method)
                return f"{m} {s}"
            return f"{s} Spirit-Forward"
        return f"{s} {f}"

    # 90%+ one family, mixed spirits
    if top_family_p >= 0.90:
        f = family_name.get(top_family, top_family)
        if top_family == 'sour':
            if top_method_p >= 0.80:
                m = method_name.get(top_method, top_method)
                return f"{m} Sours"
            if citrus_pct >= 0.80:
                return "Citrus Sours"
            return "Sours"
        if top_family == 'spirit_forward':
            if top_method_p >= 0.70:
                m = method_name.get(top_method, top_method)
                return f"{m} Spirit-Forward"
            return "Spirit-Forward"
        return f

    # 85%+ one spirit, mixed families
    if top_spirit_p >= 0.85:
        s = spirit_name.get(top_spirit, top_spirit)
        if top_family_p >= 0.60:
            f = family_name.get(top_family, top_family)
            return f"{s} {f}"
        return f"{s} Cocktails"

    # ─── MODERATE PURITY ───

    # 60-85% one family
    if top_family_p >= 0.60:
        f = family_name.get(top_family, top_family)

        if top_spirit_p >= 0.50:
            s = spirit_name.get(top_spirit, top_spirit)
            if top_family == 'sour' and citrus_pct >= 0.70:
                return f"{s}-Led Citrus Sours"
            return f"{s}-Led {f}"

        # Two dominant spirits
        if len(spirits_pct) >= 2 and spirits_pct[1][2] >= 0.25:
            s1 = spirit_name.get(spirits_pct[0][0], spirits_pct[0][0])
            s2 = spirit_name.get(spirits_pct[1][0], spirits_pct[1][0])
            return f"{s1} & {s2} {f}"

        if top_family == 'sour':
            if top_method_p >= 0.70:
                m = method_name.get(top_method, top_method)
                return f"{m} Sours"
            return "Mixed Sours"
        if top_family == 'spirit_forward':
            if top_method_p >= 0.70:
                m = method_name.get(top_method, top_method)
                return f"{m} Spirits"
            return "Mixed Spirit-Forward"
        return f"Mixed {f}"

    # 60%+ one spirit, mixed families
    if top_spirit_p >= 0.60:
        s = spirit_name.get(top_spirit, top_spirit)
        return f"{s} Mix"

    # ─── DEFINING METHOD ───
    if top_method_p >= 0.80:
        m = method_name.get(top_method, top_method)
        if top_spirit_p >= 0.40:
            s = spirit_name.get(top_spirit, top_spirit)
            return f"{m} {s} Mix"
        return f"{m} Cocktails"

    # ─── SPECIAL PATTERNS ───

    # Check for the "complex modifier sours" pattern
    # (chartreuse, maraschino, aperol, amaro, fernet - unusual modifiers in sours)
    complex_mods = sum(a['ingredients'].get(c, 0) for c in
                       ['green_chartreuse', 'yellow_chartreuse', 'maraschino',
                        'aperol', 'amaro_nonino', 'fernet_branca', 'cynar',
                        'benedictine', 'creme_de_violette'])
    if complex_mods / n >= 1.5 and top_family_p >= 0.50 and top_family == 'sour':
        return "Complex Modifier Sours"

    # Herbal liqueurs prominent
    herbal = sum(a['ingredients'].get(c, 0) for c in
                 ['green_chartreuse', 'yellow_chartreuse', 'benedictine'])
    if herbal / n >= 0.50:
        return "Herbal & Botanical"

    # ─── TWO-AXIS DESCRIPTIONS ───
    if len(spirits_pct) >= 2 and spirits_pct[0][2] >= 0.30 and spirits_pct[1][2] >= 0.25:
        s1 = spirit_name.get(spirits_pct[0][0], spirits_pct[0][0])
        s2 = spirit_name.get(spirits_pct[1][0], spirits_pct[1][0])
        if top_family_p >= 0.50:
            f = family_name.get(top_family, top_family)
            return f"{s1} & {s2} {f}"
        if top_method_p >= 0.60:
            m = method_name.get(top_method, top_method)
            return f"{m} {s1} & {s2}"
        return f"{s1} & {s2} Mix"

    # ─── LARGE CATCHALL CLUSTERS ───
    if n >= 30:
        if top_spirit_p >= 0.40:
            s = spirit_name.get(top_spirit, top_spirit)
            if top_family_p >= 0.50:
                f = family_name.get(top_family, top_family)
                return f"Broad {s} {f}"
            return f"Broad {s} Collection"
        if top_family_p >= 0.50:
            f = family_name.get(top_family, top_family)
            return f"Broad {f} Collection"
        return "Cross-Category Mix"

    # ─── FALLBACK ───
    if top_spirit_p >= 0.35:
        s = spirit_name.get(top_spirit, top_spirit)
        return f"{s}-Leaning Mix"

    return "Mixed Cocktails"


def deduplicate_names(name_map):
    """When multiple clusters share a name, differentiate by what's actually different."""
    spirit_name_map = {
        'gin': 'Gin', 'whiskey': 'Whiskey', 'rum': 'Rum',
        'agave': 'Agave', 'brandy': 'Brandy', 'vermouth': 'Vermouth',
        'amaro': 'Amaro', 'mixed': 'Mixed', 'bitters': 'Bitters',
        'herbal_liqueur': 'Herbal', 'other': 'Other',
    }

    max_rounds = 5
    for _ in range(max_rounds):
        name_counts = Counter(name_map.values())
        dupes = {name for name, count in name_counts.items() if count > 1}
        if not dupes:
            break

        for name in dupes:
            matching_hashes = [h for h, n in name_map.items() if n == name]
            # Analyze each cluster to find distinguishing features
            analyses = {}
            for h in matching_hashes:
                members = cluster_members_by_hash.get(h, [])
                analyses[h] = analyze_cluster(members)

            # Strategy 1: Differentiate by size if sizes are very different
            sizes = {h: a['n'] for h, a in analyses.items()}
            size_range = max(sizes.values()) - min(sizes.values())

            if size_range >= 5:
                # Sort by size, assign numbered names
                sorted_by_size = sorted(matching_hashes, key=lambda h: sizes[h])
                for h in sorted_by_size:
                    n = sizes[h]
                    name_map[h] = f"{name} ({n})"
                continue

            # Strategy 2: Differentiate by the spirit that differs most
            all_spirits = set()
            for a in analyses.values():
                all_spirits.update(a['spirits'].keys())

            best_diff_feature = None
            best_diff_score = 0
            for spirit in all_spirits:
                pcts = [a['spirits'].get(spirit, 0) / a['n'] for a in analyses.values()]
                diff = max(pcts) - min(pcts)
                if diff > best_diff_score:
                    best_diff_score = diff
                    best_diff_feature = ('spirit', spirit)

            # Also check methods
            for method in ['stirred', 'shaken', 'built']:
                pcts = [a['methods'].get(method, 0) / a['n'] for a in analyses.values()]
                diff = max(pcts) - min(pcts)
                if diff > best_diff_score:
                    best_diff_score = diff
                    best_diff_feature = ('method', method)

            if best_diff_feature and best_diff_score >= 0.15:
                feat_type, feat_val = best_diff_feature
                for h in matching_hashes:
                    a = analyses[h]
                    if feat_type == 'spirit':
                        pct_val = a['spirits'].get(feat_val, 0) / a['n']
                        label = spirit_name_map.get(feat_val, feat_val)
                        if pct_val >= 0.3:
                            name_map[h] = f"{name}, More {label}"
                        else:
                            name_map[h] = f"{name}, Less {label}"
                    elif feat_type == 'method':
                        pct_val = a['methods'].get(feat_val, 0) / a['n']
                        if pct_val >= 0.4:
                            name_map[h] = f"{name}, More {feat_val.title()}"
                        else:
                            name_map[h] = f"{name}, Less {feat_val.title()}"
                continue

            # Strategy 3: Just use cluster size as a last resort
            for h in matching_hashes:
                n = sizes[h]
                name_map[h] = f"{name} ({n})"

    # Final pass: if STILL duplicates after all rounds, append a/b/c
    name_counts = Counter(name_map.values())
    for name in [n for n, c in name_counts.items() if c > 1]:
        matching = [h for h, n in name_map.items() if n == name]
        matching.sort(key=lambda h: len(cluster_members_by_hash.get(h, [])))
        for i, h in enumerate(matching):
            if i > 0:  # keep first one as-is
                name_map[h] = f"{name} ({chr(97+i)})"  # a, b, c...

    return name_map


# ─── BUILD UNIQUE COMPOSITIONS AND NAME THEM ───

# First pass: collect unique compositions by hash
unique_compositions = {}
cluster_members_by_hash = {}

for ck, cv in data['clusterings'].items():
    clusters = {}
    for name, cid in cv['assignments'].items():
        cid = str(cid)
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(name)

    for cid, members in clusters.items():
        key = hashlib.md5(','.join(sorted(members)).encode()).hexdigest()[:12]
        if key not in cluster_members_by_hash:
            cluster_members_by_hash[key] = sorted(members)

# Name each unique composition
name_map = {}
for h, members in cluster_members_by_hash.items():
    name_map[h] = name_cluster(members)

# Deduplicate
name_map = deduplicate_names(name_map)

# Report
print(f"Named {len(name_map)} unique clusters")
print(f"\nName distribution:")
name_counts = Counter(name_map.values())
for name, count in name_counts.most_common(20):
    if count > 1:
        print(f"  DUPLICATE: '{name}' x{count}")

# Show names for the scenario clusters
print("\n" + "="*60)
print("SCENARIO CLUSTER NAMES")
print("="*60)

with open('viz/cluster_hash_mapping.json') as f:
    mapping = json.load(f)

scenarios = [
    'alpha_0.0_k=8', 'alpha_0.15_k=4', 'alpha_0.55_k=3', 'alpha_1.0_k=3',
    'alpha_0.15_k=2', 'alpha_0.0_k=3', 'alpha_0.0_k=10',
]

for ck in scenarios:
    cv = data['clusterings'].get(ck)
    if not cv: continue
    print(f"\n{ck} (sil={cv['silhouette']:.3f}):")

    clusters = {}
    for name, cid in cv['assignments'].items():
        cid = str(cid)
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(name)

    for cid in sorted(clusters.keys(), key=int):
        h = mapping.get(f'{ck}::{cid}', '???')
        cluster_name = name_map.get(h, f'Cluster {cid}')
        n = len(clusters[cid])
        # Show a few members
        display = [data['recipes'][m]['display_name'] for m in sorted(clusters[cid])[:5]]
        print(f"  [{cid}] {cluster_name} ({n}) — e.g. {', '.join(display)}")

# Save
with open('viz/cluster_names_v2.json', 'w') as f:
    json.dump(name_map, f, indent=2)
print(f"\nWrote viz/cluster_names_v2.json")
