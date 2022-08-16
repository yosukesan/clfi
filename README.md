# edinet_tools

A fetching tool for Edinet.

# How to use

1. Fetch metadata from Edinet server. This makes local metadata (~/.cache/yaxbrl/edinet.json)

```
python3 edinet_tools.py --update
```

2. Get all XBRL data from Edinet server. Data is stored at ./XBRL

```
python3 edinet_tools.py --all
```

3. Get target firm data

```
python3 edinet_tools.py --target トヨタ自動車株式会社
```
