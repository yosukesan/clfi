#!/usr/bin/env python3

import os, json, logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from edinet import EdinetTool

if __name__=="__main__":
    import sys
    import argparse

    cmd_parser = argparse.ArgumentParser(description='Edinet tool')
    cmd_parser.add_argument('--update', nargs='?', const=True, help='update cache data')
    cmd_parser.add_argument('--all', nargs='?', const=True, help='download all avalible data')
    cmd_parser.add_argument('--target', metavar='${target_firm}', type=str, nargs=1, help='get target_firms data')
    cmd_parser.add_argument('--clean', nargs='?', const=True, help='clean local cache ~/.cache/yaxbrl/edinet_cache.json')

    args = cmd_parser.parse_args()

    edinet = EdinetTool()

    edinet.xbrl_dir_root = 'XBRL_raw'
    home_dir = os.path.expanduser('~')
    edinet.cache_dir_path = os.path.join(home_dir, '.cache', 'yaxbrl')
    edinet.cache_file_path = os.path.join(edinet.cache_dir_path, 'edinet_cache.json')
    edinet.base_url = "https://disclosure.edinet-fsa.go.jp/api/v1"

    start: datetime = datetime(2023,1,30)
    end: datetime = datetime(2022,9,30)
    start = start.date()
    end = end.date()

    print('query ragen over: ', start, end)

    if args.update:
        print("fetching Edinet server")
        edinet.yaxbrl_update(start, end)
        sys.exit(0)

    if args.target:
        print("downloading target xbrl files")

        # only support single frim for this option
        edinet.yaxbrl_query_get(start, end, firm=args.target[0], is_exclude_fund=True)
        sys.exit(0)

    if args.all:
        print("downloading all xbrl files")

        targets = edinet.jpx_and_edinet_ticker_match()
        edinet.yaxbrl_query_get(start, end, targets, is_exclude_fund=True)

        #edinet.yaxbrl_get(start, end, is_exclude_fund=True)
        sys.exit(0)
