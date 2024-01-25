import json

with open('charset.json', 'r') as f:
    cs = json.load(f)
for ch in cs:
    cs[ch] = tuple([tuple(coord) for coord in cs[ch]])

for ch in cs:
    print(ch, cs[ch])
