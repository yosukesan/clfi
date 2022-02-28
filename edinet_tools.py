# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, timedelta
import json
import urllib.request
import os

class Edinet:

    def __init__(self, url):
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

    def _unzip(self, target_path)->None:
        import zipfile

        with zipfile.ZipFile(target_path) as data_zip:
            target_file = list(filter(lambda x: x[-4:]=="xbrl", data_zip.namelist()))
            xbrl_file_path = list(filter(lambda x: "PublicDoc" in x, target_file))             

            if len(xbrl_file_path) != 1:
                return

            comped = str(*xbrl_file_path)
            decomp = str(*xbrl_file_path)
            decomp = decomp[:-5]
            data_zip.extract(comped, decomp)

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

                key = i["filerName"]
                doc_id = i["docID"]
                hashmap[key] = i

        return hashmap

    def xbrl_get(self, target_dir, hashmap):
    #" download XBRL file from Edinet "

        for i in hashmap.keys(): 
            doc_id = hashmap[i]["docID"]

            url = self._url + "/documents/" + doc_id + "?type=1"
            print(url)
            xbrl_data = urllib.request.urlopen(url)

            pwd = os.path.join(os.getcwd(), target_dir, hashmap[i]['filerName'], hashmap[i]['docDescription'])
            os.makedirs(pwd, exist_ok=True)

            target_path = os.path.join(pwd, hashmap[i]['docID']+".zip")
            open(target_path, "wb").write(xbrl_data.read())

            self._unzip(target_path)


if __name__=="__main__":

    start: datetime = datetime(2021, 10, 14)
    end: datetime = datetime(2021, 10, 14)

    url = "https://disclosure.edinet-fsa.go.jp/api/v1"
    edinet = Edinet(url)
    metadata_json = edinet.metadata_get(start, end)

    edinet.xbrl_get("XBRL_files", metadata_json)
