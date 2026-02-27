#!/usr/bin/env python3
"""Extract cluster compositions with recipe context for LLM naming."""
import json
import hashlib

with open('viz/clustering_data.json') as f:
    data = json.load(f)

# Build unique cluster compositions with full recipe context
unique_compositions = {}  # hash -> {members, metadata, used_in}

for ck, cv in data['clusterings'].items():
    clusters = {}
    for name, cid in cv['assignments'].items():
        cid = str(cid)
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(name)

    for cid, members in clusters.items():
        key = hashlib.md5(','.join(sorted(members)).encode()).hexdigest()[:12]
        if key not in unique_compositions:
            # Build rich context
            member_details = []
            spirits = {}
            families = {}
            methods = {}
            all_ingredients = {}

            for m in sorted(members):
                r = data['recipes'].get(m, {})
                spirit = r.get('base_spirit', 'unknown')
                family = r.get('family', 'unknown')
                method = r.get('method', 'unknown')
                ingredients = r.get('ingredients', [])
                display = r.get('display_name', m)

                spirits[spirit] = spirits.get(spirit, 0) + 1
                families[family] = families.get(family, 0) + 1
                methods[method] = methods.get(method, 0) + 1
                for ing in ingredients:
                    all_ingredients[ing] = all_ingredients.get(ing, 0) + 1

                member_details.append({
                    'name': display,
                    'key': m,
                    'spirit': spirit,
                    'family': family,
                    'method': method,
                    'ingredients': ingredients,
                })

            n = len(members)
            unique_compositions[key] = {
                'hash': key,
                'size': n,
                'members': member_details,
                'spirit_breakdown': {k: f'{v}/{n}' for k, v in sorted(spirits.items(), key=lambda x: -x[1])},
                'family_breakdown': {k: f'{v}/{n}' for k, v in sorted(families.items(), key=lambda x: -x[1])},
                'method_breakdown': {k: f'{v}/{n}' for k, v in sorted(methods.items(), key=lambda x: -x[1])},
                'common_ingredients': {k: v for k, v in sorted(all_ingredients.items(), key=lambda x: -x[1])[:10]},
                'used_in': [],
            }

        unique_compositions[key]['used_in'].append(f'{ck}::{cid}')

# Also build the full mapping: clustering_key::cluster_id -> hash
mapping = {}
for ck, cv in data['clusterings'].items():
    clusters = {}
    for name, cid in cv['assignments'].items():
        cid = str(cid)
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(name)

    for cid, members in clusters.items():
        key = hashlib.md5(','.join(sorted(members)).encode()).hexdigest()[:12]
        mapping[f'{ck}::{cid}'] = key

# Write the unique compositions for naming
comps_list = sorted(unique_compositions.values(), key=lambda x: -x['size'])
with open('viz/clusters_to_name.json', 'w') as f:
    json.dump(comps_list, f, indent=2)

# Write the mapping
with open('viz/cluster_hash_mapping.json', 'w') as f:
    json.dump(mapping, f, indent=2)

print(f'Unique compositions: {len(comps_list)}')
print(f'Total cluster instances: {len(mapping)}')
print(f'Wrote viz/clusters_to_name.json')
print(f'Wrote viz/cluster_hash_mapping.json')
