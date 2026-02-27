#!/usr/bin/env python3
"""Build the comprehensive data JSON for the interactive visualization."""
import json

with open('data/embeddings.json') as f:
    emb = json.load(f)
with open('viz/clustering_exploration/alpha_spectrum_results.json') as f:
    alpha = json.load(f)
with open('viz/clustering_exploration/tau_spectrum_results.json') as f:
    tau = json.load(f)

cocktail_names = list(emb['recipes'].keys())

output = {
    'cocktail_order': cocktail_names,
    'recipes': {},
    'strategies': {},
    'clusterings': {}
}

# Recipes
for name, recipe in emb['recipes'].items():
    output['recipes'][name] = {
        'base_spirit': recipe.get('base_spirit', 'unknown'),
        'family': recipe.get('family', 'unknown'),
        'method': recipe.get('method', 'unknown'),
        'served': recipe.get('served', 'unknown'),
        'ingredients': [c['ingredient'] for c in recipe.get('components', [])],
        'display_name': name.replace('_', ' ').title()
    }

# Strategies (x,y points)
for sname, sdata in emb['strategies'].items():
    if sdata.get('points') and len(sdata['points']) > 0:
        output['strategies'][sname] = {
            'description': sdata.get('description', ''),
            'points': sdata['points']
        }

# Alpha clusterings
for alpha_key in sorted(alpha.keys()):
    adata = alpha[alpha_key]
    alpha_val = adata.get('alpha_value', alpha_key.replace('alpha_', ''))
    strategy_name = adata.get('strategy', '')

    km_results = adata.get('algorithms', {}).get('kmeans', {}).get('results', {})
    for k_key, k_data in km_results.items():
        if 'analysis' not in k_data or 'clusters' not in k_data['analysis']:
            continue
        cluster_map = {}
        for cid, cdata in k_data['analysis']['clusters'].items():
            for member in cdata['members']:
                cluster_map[member] = int(cid)

        ckey = f'alpha_{alpha_val}_{k_key}'
        output['clusterings'][ckey] = {
            'description': f'Alpha={alpha_val} {k_key}',
            'strategy': strategy_name,
            'silhouette': k_data.get('silhouette', 0),
            'n_clusters': len(set(cluster_map.values())),
            'assignments': cluster_map
        }

# Tau clusterings
for tau_key in sorted(tau.keys()):
    td = tau[tau_key]
    tv = td.get('tau_value', tau_key.replace('tau_', ''))
    desc = td.get('description', '')
    km = td.get('algorithms', {}).get('kmeans', {})

    for k_val in sorted(km.keys()):
        kd = km[k_val]
        if not isinstance(kd, dict) or 'labels' not in kd:
            continue
        labels = kd['labels']
        if len(labels) != len(cocktail_names):
            continue

        cluster_map = {}
        for i, label in enumerate(labels):
            cluster_map[cocktail_names[i]] = label

        sil = kd.get('silhouette', 0)
        ckey = f'tau_{tv}_k={k_val}'
        output['clusterings'][ckey] = {
            'description': f'Tau={tv} ({desc}) k={k_val}',
            'strategy': 'blend_struct_a000',
            'silhouette': sil if isinstance(sil, (int, float)) else 0,
            'n_clusters': len(set(labels)),
            'assignments': cluster_map
        }

print(f'Recipes: {len(output["recipes"])}')
print(f'Strategies: {len(output["strategies"])}')
print(f'Clusterings: {len(output["clusterings"])}')
print()
for ck in sorted(output['clusterings'].keys()):
    cv = output['clusterings'][ck]
    n = len(cv['assignments'])
    nc = cv['n_clusters']
    s = cv['silhouette']
    print(f'  {ck}: {nc} clusters, {n} cocktails, sil={s:.3f}')

with open('viz/clustering_data.json', 'w') as f:
    json.dump(output, f)
print(f'\nWrote viz/clustering_data.json')
