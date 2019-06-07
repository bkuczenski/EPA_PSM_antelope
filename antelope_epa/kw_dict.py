import xlrd


def mk_kwd(filename, sheet, kwcols=1, lower=True, strict=True):
    """
    Create a keyword dictionary from an excel spreadsheet.  THe keys into the dict are taken from the first k
    columns.  If k == 1, only the first column is used. If k > 1, a tuple is constructed from the first k columns.

    The values are themselves dicts whose keys are taken from the header rows after kwcols columns, and whose values
    are taken from the corresponding columns of each row.

    The 'None' key returns a tuple of length kwcols that reports the names of the header columns used to generate the
    keys.

    :param filename: path to workbook file
    :param sheet: sheet name to read
    :param kwcols: [1] number of columns to use for keys
    :param lower: [True] whether to lowercase dict keys
    :param strict: [True] whether to raise an error if the same key is encountered twice
    :return:
    """
    _kwd = dict()

    _xl = xlrd.open_workbook(filename)
    _s = _xl.sheet_by_name(sheet)

    def _s_cell(r, c):
        _cell = _s.cell(r, c)
        if _cell.ctype == 2:  # numeric
            return _cell.value
        return _s.cell(r, c).value.strip()

    def _k_cell(r, c):
        if lower:
            return _s_cell(r, c).lower()
        return _s_cell(r, c)

    for row in range(1, _s.nrows):
        if kwcols == 1:
            key = _k_cell(row, 0)
        else:
            key = tuple(_k_cell(row, k) for k in range(kwcols))
        if key in _kwd and strict:
            raise KeyError('Key %s already exists' % key)
        _kwd[key] = {_k_cell(0, k): _s_cell(row, k) for k in range(kwcols, _s.ncols)}

    _kwd[None] = tuple(_k_cell(0, k) for k in range(kwcols))
    return _kwd
