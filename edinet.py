# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, timedelta

import json
import logging
import os
import urllib.request

class Types:

    def rdict(self):
        return defaultdict(self.rdict)

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

        types = Types()
        hashmap = types.rdict()

        for d in range((end-start).days+1): 

            day = start + timedelta(d)
            str_day = str(day).split(' ')[0]

            url_date="date=" + str_day
            url = self.base_url + "/documents.json?" + url_date +"&type=2"

            metadata_json = urllib.request.urlopen(url)

            json_data = json.loads(metadata_json.read().decode())

            for i in json_data["results"]:

                if not i["docTypeCode"] in self._doc_type_codes.keys():
                    continue

                doc_type = self._doc_type_codes[i["docTypeCode"]]

                key = i["filerName"]

                hashmap[key][str_day][doc_type] = i

        return hashmap

    def xbrl_get2(self, xbrl_dir_root, hashmap, is_exclude_fund):

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
                    xbrl_data = urllib.request.urlopen(url)

                    pwd = os.path.join(os.getcwd(), xbrl_dir_root, hashed['filerName'], hashed['docDescription'])
                    os.makedirs(pwd, exist_ok=True)

                    target_path = os.path.join(pwd, hashed['docID']+".zip")
                    open(target_path, "wb").write(xbrl_data.read())
                    xbrl_file_path = self._unzip(target_path)

                    print('{0},{1},{2},{3},{4},{5}'.format(firms, doc_types, dates,doc_id, xbrl_file_path, target_path))


    def xbrl_get_by_query(self, xbrl_dir_root, hashmap, firm, is_exclude_fund):

        for dates in hashmap[firm]:
            for docs in hashmap[firm][dates]:
                hashed = hashmap[firm][dates][docs]

                doc_id = hashed['docID']

                url = '{0}/documents/{1}?type=1'\
                    .format(self.base_url, doc_id)
                xbrl_data = urllib.request.urlopen(url)

                pwd = os.path.join(os.getcwd(), xbrl_dir_root, hashed['filerName'], hashed['docDescription'])
                os.makedirs(pwd, exist_ok=True)

                target_path = os.path.join(pwd, hashed['docID']+".zip")
                open(target_path, "wb").write(xbrl_data.read())
                xbrl_file_path = self._unzip(target_path)

                print('{0},{1},{2},{3},{4}'.format(firm, dates, doc_id, xbrl_file_path, target_path))
