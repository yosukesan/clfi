#!/usr/bin/env python3

from datetime import datetime

import json
import os
import sys
import requests
import pandas as pd
import time

from edinet_utils import deep_union

DELAY = 3

class EdinetTool:

    def __init__(self):
        self._doc_type_codes = {"010": "有価証券通知書",
                                "020": "変更通知書(有価証券通知書)",
                                "030": "有価証券届出書",
                                "040": "訂正有価証券届出書",
                                "050": "届出の取り下げ願い",
                                "120": "有価証券報告書",
                                "130": "訂正有価証券報告書",
                                "140": "四半期報告書",
                                "150": "訂正四半期報告書",
                                "170": "訂正半期報告書",
                                "360" : "大量保有報告書"}
        self.error_code = ["Cache file doesn't exit. Run `python edinet_tool --update`",\
                           "Cache file dir doesn't exit. Run `python edinet_tool --update`"]

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, url):
        self._base_url = url

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

    def unzip_all(self, zip_file_path, xbrl_files):
        import zipfile

        if len(xbrl_files) == 0:
            return

        with zipfile.ZipFile(zip_file_path) as data_zip:
            print('{0}:'.format(zip_file_path))
            for xbrl_file in xbrl_files:
                print('\tdeflating {0}'.format(xbrl_file))
                data_zip.extract(member=xbrl_file)

        print('')

    def is_fund(self, data):
        if not data:
            return False

        if data[0] == 'G':
            return True

        return False

    def metadata_get(self, start, end)->dict:
    #" download document.json file from Edinet "

        ses = requests.Session()
        hashmap = {}

        for d in pd.date_range(start=end, end=start): 

            url = '{0}/documents.json?date={1}&type=2'.format(self.base_url, d.strftime('%Y-%m-%d'))
            print(url)

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

                submitted_date = datetime.strptime(i['submitDateTime'], '%Y-%m-%d %H:%M')
                if submitted_date.strftime('%Y-%m-%d') not in hashmap[i["edinetCode"]]:
                    hashmap[i["edinetCode"]][submitted_date.strftime('%Y-%m-%d')] = {}

                hashmap[i["edinetCode"]][submitted_date.strftime('%Y-%m-%d')][doc_type] = i

            time.sleep(DELAY)

        ses.close()

        return hashmap

    def xbrl_get2(self, xbrl_dir_root, hashmap, is_exclude_fund):

        ses = requests.Session()

        for firms in hashmap.keys():
            for dates in hashmap[firms]:
                for doc_types in hashmap[firms][dates]:

                    hashed = hashmap[firms][dates][doc_types]

                    if is_exclude_fund == True and self.is_fund(hashed['fundCode']):
                        continue

                    if hashed['xbrlFlag'] == '0':
                        continue

                    doc_id = hashed['docID']

                    url = '{0}/documents/{1}?type=1'\
                        .format(self.base_url, doc_id)
                    resp = ses.get(url)
                    resp.encoding = resp.apparent_encoding

                    time.sleep(DELAY)

                    pwd = os.path.join(os.getcwd(), xbrl_dir_root, r'{0}'.format(hashed['filerName']), r'{0}'.format(hashed['docDescription']))
                    os.makedirs(pwd, exist_ok=True)

                    target_path = os.path.join(pwd, hashed['docID']+".zip")
                    open(target_path, "wb").write(resp.text)
                    xbrl_file_path = self._unzip(target_path)

                    print('{0},{1},{2},{3},{4},{5}'.format(firms, doc_types, dates,doc_id, xbrl_file_path, target_path))

        ses.close()
        return 

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

                    url = '{0}/documents/{1}?type=1'\
                        .format(self.base_url, doc_id)
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

    def batch_download(self, excel_file) -> dict:
        
        df = pd.read_excel(excel_file)
        df = df[df['市場・商品区分'] != 'ETF・ETN']
        df = df[['コード', '銘柄名', '33業種コード', '33業種区分', '17業種コード', '17業種区分', '規模コード', '規模区分']]

        return df

    def yaxbrl_get(self, start, end, is_exclude_fund):
    
        if not os.path.isdir(self.xbrl_dir_root):
            os.makedirs(self.xbrl_dir_root, exist_ok=True)
    
        cache_data = self.yaxbrl_read_cache_data(self.cache_file_path)
        self.xbrl_get2(self.xbrl_dir_root, cache_data, is_exclude_fund)
    
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

    def jpx_str_strip(self, text : str)->str:
        import unicodedata as ud
    
        MODE = 'NFKC'
        normalized = ud.normalize(MODE, text)
        unspaced = normalized.replace(' ', '').replace('\t', '').replace('　', '')
        return unspaced.replace('株式会社', '').replace('合同会社', '').replace('有限会社', '')

    def jpx_and_edinet_ticker_match(self)->list:
        import os
    
        df = pd.read_excel('data_j.xls')
        filtered_index = list(map(lambda x : '株式' in x, df['市場・商品区分']))
        filtered =  df[filtered_index]
        jpx_ticker = list(map(lambda x: self.jpx_str_strip(x), filtered['銘柄名'].to_list()))
        
        cache = pd.read_json('/home/yosuke/.cache/yaxbrl/edinet_cache.json')
        cached = list(map(lambda x: (self.jpx_str_strip(x), x), cache.keys()))
        
        #print('data_j.xls', len(filtered.index))
        #print('stripped', len(stripped))
        #print('tickers', len(tickers))

        return list(filter(lambda x: x[0] in jpx_ticker, cached))
