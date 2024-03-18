# edinet_tools

A fetching tool for Edinet.

# How to use

1. Fetch metadata from Edinet server. This makes local metadata (~/.cache/yaxbrl/edinet.json)

```
python edinet_tools.py --update --start=2014-01-01 --end=2022-02-11
```

note: query range need to be within 10 years due to Edinet's specification.

2. Get all XBRL data from Edinet server. Data is stored at ./XBRL

download ticker Excel from JPX and place the root dir
https://www.jpx.co.jp/markets/statistics-equities/misc/01.html

```
python3 edinet_tools.py --all
```

3. Get target firm data. The name need to be identical to registered name on Edinet.

```
python3 edinet_tools.py --target トヨタ自動車株式会社
```

# Advanced

Download CSV file called Edinet コードリスト. It's should be at the bottom of the page.
https://disclosure2.edinet-fsa.go.jp/weee0010.aspx
