"""
This function conceals key information about the foreground model to enable sharing.

It uses the same definition of "leaf" nodes versus "subassemblies" in the main package:
 - leaf nodes have no child flows
 - subassemblies appear as the "next assembly" in at least one record

Uses the same validation routine as EpaF18Foreground to identify valid sheets, and then rewrites each of them by
renaming subassembly part numbers and anonymizing assembly names, and then writes the results to new spreadsheet files
using XlsxWriter
"""

from .validation import validate_folder
from random import randint
from xlsxwriter import Workbook

import os


def _stripped_val(cell):
    if cell.ctype == 1:
        return cell.value.strip()
    return cell.value


class WorksheetAnonymizer(object):
    """
    Builds a dict of subassemblies and renames them to random assembly names, ensuring that no duplications occur
    """
    def __init__(self, folder, pattern=None):
        """

        :param folder:
        :param pattern: a lambda expression that accepts a string input and converts it to a part number. Default:
         lambda x: 'ANON_%06d' % x
        """
        self._sheets = [s for s in validate_folder(folder)]
        self._books = set(s.book for s in self._sheets)

        self._map = {'': None}
        self._rmap = dict()

        if pattern is None:
            pattern = lambda x: 'ANON_%06d' % x
        self._pattern = pattern

    def _gen_new_rand(self):
        while True:
            k = randint(1e5, 1e6)
            if k not in self._rmap:
                return k

    def _gen_new_map(self, assy):
        if assy in self._map:
            return self._map[assy]
        nr = self._gen_new_rand()
        nn = self._pattern(nr)
        self._map[assy] = nn
        self._rmap[nr] = assy
        return nn

    def _anonymize_sheet(self, s):
        """
        Identifies distinct subassemblies and assigns them random terms
        :param s:
        :return:
        """
        headers = s.row(0)
        na = next(i for i, k in enumerate(headers) if _stripped_val(k) == 'Next Assembly')
        for row in range(1, s.nrows):
            self._gen_new_map(_stripped_val(s.cell(row, na)))

    @staticmethod
    def _write_header(sheet, hdr, bold):
        map_number = None
        map_name = None
        for i, k in enumerate(hdr):
            if _stripped_val(k) == 'Part Number':
                map_number = i
            elif _stripped_val(k) == 'Part Name':
                map_name = i
            sheet.write(0, i, _stripped_val(k), bold)
        if map_name is None or map_number is None:
            raise AttributeError('header fail %s / %s' % (map_number, map_name))
        return map_number, map_name

    def _anonymize_row(self, old, new, i, map_number, map_name, bold):
        row = old.row(i)
        num = _stripped_val(row[map_number])
        if num in self._map:
            # rename if mapped
            anum = self._map[num]
            anam = '%s Sub-assembly' % anum
            _bn = True
        else:
            # retain if not mapped
            anam = _stripped_val(row[map_name])
            _bn = False
        for k, val in enumerate(row):
            do_bold = False
            if val.ctype == 0:
                continue
            aval = _stripped_val(val)
            if k == map_name:
                aval = anam
                do_bold = _bn
            elif aval in self._map:
                aval = self._map[aval]
                do_bold = True
            if do_bold:
                new.write(i, k, aval, bold)
            else:
                new.write(i, k, aval)

    def _write_next_book(self, oldbook, newbook, bold):
        for sheet in self._sheets:
            if sheet.book is not oldbook:
                continue
            self._anonymize_sheet(sheet)
            print('Adding sheet %s -> %s' % (sheet.name, self._map[sheet.name]))
            newsheet = newbook.add_worksheet(self._map[sheet.name])
            map_number, map_name = self._write_header(newsheet, sheet.row(0), bold)
            for i in range(1, sheet.nrows):
                self._anonymize_row(sheet, newsheet, i, map_number, map_name, bold)
        print('writing workbook %s' % newbook)

    def write_anon_books(self, ddir):
        if not os.path.isdir(ddir):
            if os.path.exists(ddir):
                raise ValueError
            os.makedirs(ddir, exist_ok=True)
        for i, b in enumerate(self._books):
            newbook = os.path.join(ddir, 'anonymized_%d.xlsx' % i)
            with Workbook(newbook) as wb:
                bold = wb.add_format({'bold': True})
                self._write_next_book(b, wb, bold)
