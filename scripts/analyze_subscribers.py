import csv
from collections import Counter

filepath = '/Users/borjafernandezangulo/Downloads/subscriber-export-2026-07-20-02-35-19.csv'

subscribers = []
with open(filepath, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        subscribers.append(row)

total = len(subscribers)
types = Counter(r['Type'] for r in subscribers)
activity = Counter(r['Activity'] for r in subscribers)
has_name = sum(1 for r in subscribers if r['Name'].strip())

domains = Counter(r['Email'].split('@')[-1] for r in subscribers)

dates = [r['Start date'][:10] for r in subscribers if r['Start date']]
date_spikes = Counter(dates).most_common(10)

rev_total = sum(float(r['Revenue'].replace('$', '').replace(',', '')) for r in subscribers if r['Revenue'])

print(f"TOTAL SUBSCRIBERS: {total}")
print(f"TYPES: {dict(types)}")
print(f"ACTIVITY DISTRIBUTION: {dict(sorted(activity.items()))}")
print(f"WITH NAME: {has_name} / {total}")
print(f"REVENUE TOTAL: ${rev_total:.2f}")

print("\nTOP 15 DOMAINS:")
for d, c in domains.most_common(15):
    print(f"  {d}: {c}")

print("\nTOP 10 DATE SPIKES (SIGNUPS/IMPORTS):")
for dt, c in date_spikes:
    print(f"  {dt}: {c} subs")

# Segment notable key accounts / domains
vip_keywords = ['openai', 'huggingface', 'foundersfund', 'microstrategy', 'bittensor', 'sentient', 'nillion', 'dydx', 'ninjatune', 'mixmag', 'ostgut', 'sohoradio', 'hypebeast', 'audaxrenovables', 'berria', 'media-attack', 'audioshake', 'loudwomen', 'convequity', 'securebio']

vips = [r for r in subscribers if any(k in r['Email'].lower() for k in vip_keywords)]
print(f"\nNOTABLE TECH/MEDIA/FINANCE/MUSIC ACCOUNTS ({len(vips)}):")
for v in vips[:20]:
    print(f"  - {v['Email']} (Activity: {v['Activity']}, Type: {v['Type']}, Date: {v['Start date'][:10]})")

influencer_gmails = [r for r in subscribers if 'contacto@gmail.com' in r['Email'].lower() or any(x in r['Email'].lower() for x in ['elxokas', 'wallstreetwolverine', 'alxelmundo', 'pedritoviral', 'davooxeneize', 'kiddkeo', 'dalasito', 'trilineyt'])]
print(f"\nNOTABLE CREATOR/INFLUENCER GMAILS ({len(influencer_gmails)}):")
for v in influencer_gmails[:25]:
    print(f"  - {v['Email']} (Activity: {v['Activity']}, Type: {v['Type']})")
