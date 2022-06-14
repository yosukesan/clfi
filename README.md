# edinet_tools

A fetching tool for Edinet.

# How to use

1. Fetch metadata from Edinet server. This makes local metadata (~/.cache/yaxbrl/edinet.json)

```
python3 edinet_tools.py --update
```

2. Get XBRL data from Edinet server. Data is stored at ./XBRL\_files

```
python3 edinet_tools.py --get
```
