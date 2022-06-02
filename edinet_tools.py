# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, timedelta
import json
import urllib.request
import os
import time

class Edinet:

    def __init__(self, url):
        self.delay = 1
        self._url = url
        self._doc_type_codes = {"010": "有価証券通知書",
                                "020": "変更通知書(有価証券通知書)",
                                "030": "有価証券届出書",
                                "040": "訂正有価証券届出書",
                                "050": "届出の取り下げ願い",
                                "120": "有価証券報告書",
                                "130": "訂正有価証券報告書",
                                "140": "四半期報告書",
                                "150": "訂正四半期報告書",
                                "150": "半期報告書",
                                "170": "訂正半期報告書"}

        self._data_dir = ''

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

    def metadata_get(self, start, end)->dict:
    #" download document.json file from Edinet "

        hashmap = {}

        for d in range((end-start).days+1): 

            day = start + timedelta(d)
            str_day = str(day).split(' ')[0]

            url_date="date=" + str_day
            url = self._url + "/documents.json?" + url_date +"&type=2"

            metadata_json = urllib.request.urlopen(url)

            json_data = json.loads(metadata_json.read().decode())

            for i in json_data["results"]:
                if not i["docTypeCode"] in self._doc_type_codes.keys():
                    continue

                doc_type = self._doc_type_codes[i["docTypeCode"]]
                key = i["filerName"]
                doc_id = i["docID"]
                hashmap[key] = i
                #print('name={0}, docID={1}, formCode={2}'.format(key, doc_id, i['formCode']))

            time.sleep(self.delay)

        return hashmap

    def xbrl_get(self, hashmap):
    #" download XBRL file from Edinet "
        import json

        for i in hashmap.keys(): 
            doc_id = hashmap[i]["docID"]

            url = self._url + "/documents/" + doc_id + "?type=1"
            xbrl_data = urllib.request.urlopen(url)

            pwd = os.path.join(os.getcwd(), self._data_dir, hashmap[i]['filerName'], hashmap[i]['docDescription'])
            os.makedirs(pwd, exist_ok=True)

            zip_file_path = os.path.join(pwd, hashmap[i]['docID']+".zip")

            # save zip file to local
            open(zip_file_path, "wb").write(xbrl_data.read())

            xbrl_files = self.get_xbrl_path_in_zip(zip_file_path)

            #self._unzip(target_path)
            self.unzip_all(zip_file_path, xbrl_files)

            print('{0} {1}:'.format(hashmap[i]['filerName'], len(xbrl_files)))
            for xbrl_file in xbrl_files:
                print('\t{0}'.format(xbrl_file))
            print('')

            time.sleep(self.delay)

if __name__=="__main__":

    start: datetime = datetime(2021, 10, 10)
    end: datetime = datetime(2021, 10, 13)

    url = "https://disclosure.edinet-fsa.go.jp/api/v1"
    edinet = Edinet(url)
    edinet.data_dir("XBRL_files")
    metadata_json = edinet.metadata_get(start, end)

    edinet.xbrl_get(metadata_json)
