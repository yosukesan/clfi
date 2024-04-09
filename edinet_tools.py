#!/usr/bin/env python3

import os, json, logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from edinet import EdinetTool
import getpass

if __name__=="__main__":
    import sys
    import argparse

    cmd_parser = argparse.ArgumentParser(description='Edinet tool')
    cmd_parser.add_argument('--update', nargs='?', const=True, help='update cache data')
    cmd_parser.add_argument('--all', nargs='?', const=True, help='download all avalible data')
    cmd_parser.add_argument('--target', metavar='${target_firm}', type=str, nargs=1, help='get target_firms data')
    cmd_parser.add_argument('--clean', nargs='?', const=True, help='clean local cache ~/.cache/yaxbrl/edinet_cache.json')
    cmd_parser.add_argument('--api_key')
    cmd_parser.add_argument('--start')
    cmd_parser.add_argument('--end')

    args = cmd_parser.parse_args()
    edinet = EdinetTool()

    edinet.xbrl_dir_root = 'XBRL_raw'
    home_dir = os.path.expanduser('~')
    edinet.cache_dir_path = os.path.join(home_dir, '.cache', 'yaxbrl')
    edinet.cache_file_path = os.path.join(edinet.cache_dir_path, 'edinet_cache.json')
    edinet.base_url = "https://disclosure.edinet-fsa.go.jp/api/v2"

    # parse dates
    sYYYY = int(args.start.split('-')[0])
    sMM = int(args.start.split('-')[1])
    sDD = int(args.start.split('-')[2])
    eYYYY = int(args.end.split('-')[0])
    eMM = int(args.end.split('-')[1])
    eDD = int(args.end.split('-')[2])

    start = datetime(sYYYY, sMM, sDD).date()
    end = datetime(eYYYY, eMM, eDD).date()

    # API KEY
    # if api_key is given, its batch run mode
    if not args.api_key:
        edinet.edinet_key = getpass.getpass()
    else:
        edinet.edinet_key = args.api_key

    print('query range: from {0} to {1}'.format(start, end))
    if args.update:
        print("fetching Edinet server")
        edinet.yaxbrl_update(end, start)

    elif args.target:
        print("downloading target xbrl files")

        # only support single frim for this option
        edinet.yaxbrl_query_get(end, start, firm=args.target[0], is_exclude_fund=True)
