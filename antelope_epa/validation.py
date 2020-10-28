from antelope_catalog.providers.xl_dict import XlDict
from .exceptions import DuplicateSubAssembly
import os
import xlrd


def validate_sheet(sheet):
    """
    checks whether the sheet includes references to unrecognized assemblies; returns the names of the
    unrecognized assemblies
    """
    xld = XlDict(sheet)
    seen = set()
    dups = set()
    for i, row in xld.iterrows():
        part = row['Part Number']
        if part in seen:
            dups.add(part)
        else:
            seen.add(part)

        parent = row['Next Assembly']
        if parent is not None:
            if parent not in seen:
                yield parent
            elif parent == part:
                print('Warning: parent is self: %s (row %d)' % (parent, i + 1))
            elif parent in dups:
                raise DuplicateSubAssembly('%s (row %d)' % (parent, i+1))



def validate_workbook(book):
    all_m = set()
    for n in book.sheet_names():
        s = book.sheet_by_name(n)
        m = set(k for k in validate_sheet(s))
        print('%s: %s' % (n, m))
        all_m |= m
    return all_m


def validate_folder(folder):
    """
    Generates a list of spreadsheets that pass validation
    :param folder:
    :return:
    """
    if folder is None:
        return
    asm = dict()
    mis = dict()
    xl = dict()
    xlss = [k for k in os.listdir(folder) if os.path.splitext(k)[1].lower().startswith('.xls')]
    for xls in xlss:
        try:
            xl[xls] = xlrd.open_workbook(os.path.join(folder, xls))
        except xlrd.XLRDError:
            continue
        print('Workbook: %s' % xls)
        print('Assemblies: %s' % xl[xls].sheet_names())
        asm[xls] = set(xl[xls].sheet_names())

        m = validate_workbook(xl[xls])
        print('Missing: %s\n' % m)
        mis[xls] = m
    asm_all = set(k for v in asm.values() for k in v)
    mis_all = set(k for v in mis.values() for k in v)
    print('Cross-References: %s' % (asm_all & mis_all))
    print('Globally Missing: %s' % (mis_all - asm_all))
    # get rid of files with missing references
    while 1:
        bad = []
        for k, v in mis.items():
            if len(v - asm_all) > 0:
                bad.append(k)
        if len(bad) == 0:
            break
        asm.pop(k)
        mis.pop(k)
        asm_all = set(k for v in asm.values() for k in v)
    # generate sheets from remaining files
    for k in asm.keys():
        wb = xl[k]
        for sheet in wb.sheets():
            yield sheet
