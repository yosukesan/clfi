#!/usr/bin/env python3

import json, os, requests, sys, time

from datetime import datetime
from edinet_utils import deep_union
import pandas as pd

DELAY = 3

class EdinetTool:

    def __init__(self):
        self._doc_type_codes = {
            "010": "有価証券通知書",
            "020": "変更通知書(有価証券通知書)",
            "030": "有価証券届出書",
            "040": "訂正有価証券届出書",
            "050": "届出の取り下げ願い",
            "120": "有価証券報告書",
            "130": "訂正有価証券報告書",
            "140": "四半期報告書",
            "150": "訂正四半期報告書",
            "170": "訂正半期報告書",
            "360": "大量保有報告書"}
        self.error_code = ["Cache file doesn't exit. Run `python edinet_tool --update`",\
                           "Cache file dir doesn't exit. Run `python edinet_tool --update`"]

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, url):
        self._base_url = url

    @property
    def edinet_key(self):
        return self._edinet_key

    @edinet_key.setter
    def edinet_key(self, key):
        self._edinet_key = key

    @property
    def cache_dir_path(self):
        return self._cache_dir_path

    @cache_dir_path.setter
    def cache_dir_path(self, cache_dir_path):
        self._cache_dir_path = cache_dir_path

    @property
    def cache_file_path(self):
        return self._cache_file_path

    @cache_file_path.setter
    def cache_file_path(self, cache_file_path):
        self._cache_file_path = cache_file_path

    @property
    def json_dir_path(self):
        return self._json_dir_path

    @json_dir_path.setter
    def json_dir_path(self, json_dir_path):
        self._json_dir_path

    @property
    def xbrl_dir_root(self):
        return self._xbrl_dir_root

    @xbrl_dir_root.setter
    def xbrl_dir_root(self, xbrl_dir_root):
        self._xbrl_dir_root = xbrl_dir_root

    @property
    def edinet_meta_data(self):
        return self._meta_data

    @edinet_meta_data.setter
    def edinet_meta_data(self, meta_data):
        self._meta_data = meta_data

    def data_dir(self, data_dir):
        self._data_dir = data_dir

    def get_xbrl_path_in_zip(self, target_path):
        import zipfile

        xbrl_file_path = None

        with zipfile.ZipFile(target_path) as data_zip:
            target_file = list(filter(lambda x: x[-4:]=="xbrl", data_zip.namelist()))
            xbrl_file_path = list(filter(lambda x: "PublicDoc" in x, target_file))

        return xbrl_file_path

    def _unzip(self, target_path)->None:
        import zipfile

        xbrl_file_path = self.get_xbrl_path_in_zip(target_path)

        if len(xbrl_file_path) != 1:
            return

        comped = str(*xbrl_file_path)
        decomp = str(*xbrl_file_path)
        decomp = decomp[:-5]

        with zipfile.ZipFile(target_path) as data_zip:
            data_zip.extract(comped, decomp)

        if len(xbrl_file_path) > 0:
            xbrl_file_path = xbrl_file_path[0]

        return xbrl_file_path


    def metadata_get(self, start, end)->dict:
        """
        download document.json file from Edinet
        """

        ses = requests.Session()
        hashmap = {}

        for d in pd.date_range(start=end, end=start): 

            url = '{0}/documents.json?date={1}&type=2&Subscription-Key={2}'.format(self.base_url, d.strftime('%Y-%m-%d'), self.edinet_key)

            resp = ses.get(url)
            if resp.status_code != requests.codes.ok: 
                sys.stderr.write('{0}: at metadata_get'.format(str(ConnectionError)))    
                sys.exit(2)

            resp.encoding = resp.apparent_encoding
            json_data = json.loads(resp.text)

            for i in json_data["results"]:

                if i['seqNumber'] == None:
                    continue

                if i["docTypeCode"] not in self._doc_type_codes.keys():
                    continue

                doc_type = self._doc_type_codes[i["docTypeCode"]]

                if i["edinetCode"] not in hashmap.keys():
                    hashmap[i["edinetCode"]] = {}

                period_end = datetime.strptime(i['periodEnd'], '%Y-%m-%d %H:%M')
                period_end = period_end.strftime('%Y-%m-%d')
                if period_end not in hashmap[i["edinetCode"]]:
                    hashmap[i["edinetCode"]][period_end] = {}

                hashmap[i["edinetCode"]][period_end][doc_type] = i

            time.sleep(DELAY)

            print(d.date())

        ses.close()

        return hashmap


    def xbrl_get_by_query(self, xbrl_dir_root, hashmap, targets, is_exclude_fund):
        import unicodedata

        ses = requests.Session()

        firms = []
        if isinstance(targets, str):
            # need to make tuple. First element is dummy.
            firms.append(('dummy_element', targets))

        if isinstance(targets, list):
            firms = targets

        for item in firms:
            if len(item) == 1:
                Warning('Unmatched JPX ticker to Edinet data. Skipping.')
                continue
            firm = item[1] 
            print('{0},,,,'.format(firm))
            for dates in hashmap[firm]:
                for docs in hashmap[firm][dates]:
                    hashed = hashmap[firm][dates][docs]

                    doc_id = hashed['docID']

                    url = '{0}/documents/{1}?type=1&Subscription-Key={2}'\
                        .format(self.base_url, doc_id, self.edinet_key)
                    resp = ses.get(url)

                    if resp.status_code != requests.codes.ok:
                        sys.stderr.write('{0} at xbrl_get_by_query'.format(ConnectionError))
                        sys.exit(1)

                    resp.encoding = resp.apparent_encoding

                    time.sleep(DELAY)

                    pwd = unicodedata.normalize('NFKC', os.path.join(os.getcwd(), xbrl_dir_root, hashed['filerName'], hashed['docDescription'].replace('/', '')))
                    pwd = pwd.replace('(', '').replace(')', '')
                    os.makedirs(pwd, exist_ok=True)

                    target_path = os.path.join(pwd, hashed['docID']+".zip")
                    open(target_path, "wb").write(resp.content)
                    xbrl_file_path = self._unzip(target_path)

                    print('{0},{1},{2},{3},{4}'.format(firm, dates, doc_id, xbrl_file_path, target_path))

        ses.close()

    def xbrl_filter_by_dates(self, hashmap, start, end):

        new_hash = {}

        for firm in hashmap:
            new_hash[firm] = {}
            for dates in hashmap[firm]:
                if datetime.strptime(dates, '%Y-%m-%d').date() >= end:
                    new_hash[firm][dates] = hashmap[firm][dates]

        return new_hash


    def yaxbrl_query_get(self, start, end, firm, is_exclude_fund):
    
        cache_data = self.yaxbrl_read_cache_data(self.cache_file_path)
        cache_data = self.xbrl_filter_by_dates(cache_data, start, end)
        self.xbrl_get_by_query(self.xbrl_dir_root, cache_data, firm, is_exclude_fund)

    def yaxbrl_read_cache_data(self, file_path):
    
        if not os.path.isfile(file_path):
            logging.error('@{0}: Error number = {1}\n\t{2}' \
                .format(yaxbrl_get.__name__, 0, self.error_code[0]))
            sys.exit(1)
    
        rfile = open(self.cache_file_path, 'r')
        cache_data = json.load(rfile)
        rfile.close()
    
        return cache_data
    
    def yaxbrl_update(self, start, end):
    
        new_data = self.metadata_get(start, end)
        previous_data = {}
    
        if not os.path.isdir(self.cache_dir_path):
            print('making local cache dir : ', self.cache_dir_path)
            os.makedirs(self.cache_dir_path)
        else:
            if os.path.isfile(self.cache_file_path):
                print('reading local cache file : ', self.cache_file_path)
                BUFFERED = new_data.keys()
                with open(self.cache_file_path) as rfile:
                    previous_data = json.load(rfile)
                new_data = deep_union(new_data, previous_data)

        print('Downloading meta json file')
        with open(self.cache_file_path, 'w') as wfile:
            json.dump(new_data, wfile)
