# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Riccardo Magliocchetti (riccardo.magliocchetti@gmail.com)
#
# This file is licensed under the terms of the GNU General Public
# License version 2. This program is licensed "as is" without any
# warranty of any kind, whether express or implied.

from pdftables import get_tables
import sys
import requests
import time
import os.path
import csv
import json


class GoogleQueryLimit(Exception):
    pass


class Cache(object):
    """
    Simple cache object to save queries to google geocode api
    """
    def __init__(self, filename=None):
        if not filename:
            filename = 'geocode.cache'
        self._filename = filename

        self._cache = {}
        try:
            with open(filename, 'r') as f:
                self._cache = json.load(f)
        except Exception, e:
            print(e)

    def __contains__(self, item):
        return item in self._cache

    def __getitem__(self, item):
        if item.startswith('_'):
            return gettattr(self, item)
        return self._cache[item]

    def __setitem__(self, key, item):
        if key.startswith('_'):
            setattr(self, key, item)
        self._cache[key] = item

    def dump(self):
        with open(self._filename, 'w') as f:
            json.dump(self._cache, f)


class RowCleaner(object):
    def cell_content_is_dup(self, cell):
        l = len(cell)
        if l % 2:
            return False
        edge = l // 2
        return cell[:edge] == cell[edge:]

    def get_row(self, row):
        """
        The first element should be a string that would used to query google
        Return None if want to skip the line
        """
        return row


class GttAbbRowCleaner(RowCleaner):
    """
    TABLE HEADER:
           0                   1         2        3     4      5                   6    7
    --------------------------------------------------------------------------------------
    |    VIA|          INDIRIZZO|N° CIVICO| INTERNO|  CAP|CITTA'|     TIPO ESERCIZIO| BIP|
    """
    def cell_dedup(self, cell):
        l = len(cell)
        edge = l // 2
        # we pick the last occurence because the first hunk of CAP is messed up
        return cell[edge:]

    def get_row(self, row):
        """
        Cleanup row data:
        - merge address
        - workaround getting duplicated content for the same cell
        Output format:
        (address, point of sale description, supports bip card)
        """
        # we are not parsing multi line cell correctly, just skip fscked entries
        if not all([row[0], row[1], row[4], row[5]]):
            return None

        # sometimes we get the same content duplicated
        if self.cell_content_is_dup(row[0]):
            row = map(self.cell_dedup, row)

        return (u"{} {} {} {}, {}, {}".format(row[0], row[1], row[2], row[3], row[4], row[5]),
                unicode(row[6]),
                "CARTA BIP" if row[7] == "SI" else "",
        )


class GeoPdfExtractor(object):
    def __init__(self, filenames, google_key=None):
        self.pdfs = filenames
        self.key = google_key
        self.parsed_data = None
        name, ext = os.path.splitext(os.path.basename(filenames[0]))
        self.project_name = name

        self.locations = None
        self.errors = None

    def parse_pdf_files(self, cleaner=None):
        """
        The cleaner parameter should be an instance of RowCleaner
        """
        data = []

        if not cleaner:
           cleaner = RowCleaner
        row_cleaner = cleaner()

        for file in self.pdfs:
            with open(file, 'rb') as f:
                tables = get_tables(f)
                rows = [row_cleaner.get_row(row) for table in tables for row in table]
                data.extend([row for row in rows if row])
        self.parsed_data = data

    def google_geocode(self, address):
        print("Google geocode: {}".format(address))

        # google limit for free usage is 5 rps, let's sleep a bit
        time.sleep(0.2)

        payload = {'key': self.key, 'address': address}
        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=payload)
        r.raise_for_status()
        data = r.json()
        if data['status'] == 'OVER_QUERY_LIMIT':
           raise GoogleQueryLimit
        if data['status'] != 'OK':
           raise
        location = data['results'][0]['geometry']['location']
        return (location['lat'], location['lng'])

    def add_geo_positions(self):
        self.errors = []
        self.locations = []
        cache = Cache()
        for place in self.parsed_data:
            address = place[0]
            if address not in cache:
                try:
                    cache[address] = self.google_geocode(address)
                except GoogleQueryLimit:
                    raise
                except Exception, e:
                    self.errors.append(place)
                    continue
            lat, lng = cache[address]
            self.locations.append(place + ("{:.5f}".format(lat), "{:.5f}".format(lng)))
        cache.dump()

    def dump_csv(self, header, filename=None):
        if filename is None:
            filename = self.project_name + '.csv'

        with open(filename, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            writer.writerows(self.locations)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        extractor = GeoPdfExtractor(sys.argv[2:], google_key=sys.argv[1])
        extractor.parse_pdf_files(cleaner=GttAbbRowCleaner)
        try:
            extractor.add_geo_positions()
        except GoogleQueryLimit:
            print("Google query limit reached: bye!")
        else:
            extractor.dump_csv(header=["Indirizzo", "Tipologia", "Carta BIP", "Lat", "Lng"])
    else:
        print("Usage: {} <google-key> <file.pdf>".format(sys.argv[0]))
