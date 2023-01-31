# edinet_tools

A fetching tool for Edinet.

# How to use

1. Fetch metadata from Edinet server. This makes local metadata (~/.cache/yaxbrl/edinet.json)

```
python3 edinet_tools.py --update
```

2. Get all XBRL data from Edinet server. Data is stored at ./XBRL

Need to download excel spread sheet here and place the project root dir.
https://www.jpx.co.jp/markets/statistics-equities/misc/01.html

The run.
```
python3 edinet_tools.py --all
```

3. Get target firm data

```
python3 edinet_tools.py --target トヨタ自動車株式会社
```
