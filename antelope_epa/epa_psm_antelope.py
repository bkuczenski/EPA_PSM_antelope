import os
from antelope_catalog.providers.xl_dict import XlDict

from .validation import validate_folder
from .exceptions import DuplicateSubAssembly


class EpaF18Foreground(object):
    """
    This class is used to read in spreadsheets as formatted for the EPA PSM hackathon, and create product systems
    from them.
    """
    _folder = None
    _valid_sheets = ()
    _refs = []

    def __init__(self, foreground, folder=None):
        """

        :param foreground: an Antelope foreground interface
        :param folder: [None] directory containing source files
        """
        self._fg = foreground
        self.folder = folder

    @property
    def fg(self):
        return self._fg

    @property
    def folder(self):
        return self._folder

    @folder.setter
    def folder(self, value):
        if value is None:
            return
        if self._folder is not None:
            raise AttributeError('Folder already set to %s' % self._folder)
        path = os.path.abspath(value)
        if not os.path.isdir(path):
            raise ValueError('Path is not a directory: %s' % path)
        self._folder = path
        self._valid_sheets = tuple(validate_folder(path))
        print('Valid assemblies: %s' % [k for k in self.valid_sheets])

    @property
    def valid_sheets(self):
        for s in self._valid_sheets:
            yield s.name

    '''
    Fragment Building
    '''

    def _row_to_flow(self, row):
        """
        This function is specific to the EPA foregrounds and should be the final disposition of the row dict.
        Part Number is popped to retrieve flow.  Part Name is popped to set flow name.
        """
        if 'Next Assembly' in row:
            raise AttributeError('"Next Assembly" should be popped')
        flow_ref = row.pop('Part Number')
        if flow_ref is None:
            raise ValueError('Part number cannot be none')
        flow_name = row.pop('Part Name')
        if flow_name is None:
            flow_name = '%s ASSEMBLY' % flow_ref
        flow = self.fg[flow_ref]
        if flow is None:
            flow = self.fg.new_flow(flow_name, 'Number of items', external_ref=flow_ref, **row)
            if self.fg[flow_ref] is not flow:
                raise KeyError('Flow ref %s failed to properly register' % flow_ref)
        return flow

    def _get_next_name(self, flow):
        parent_ref = '%s ASSEMBLY' % flow.external_ref
        if self.fg[parent_ref] is not None:
            _ac = 0
            while True:
                parent_ref = '%s ASSEMBLY alt %d' % (flow.external_ref, _ac)
                if self.fg[parent_ref] is not None:
                    _ac += 1
                    continue
                break
        return parent_ref

    def _new_reference_fragment(self, flow, **kwargs):
        # create a new parent fragment
        parent_ref = self._get_next_name(flow)
        frag = self.fg.new_fragment(flow, 'Output', Name=parent_ref, **kwargs)
        self.fg.name_fragment(frag, parent_ref)
        return frag

    def _process_row(self, i_row, source):
        i, row = i_row
        i += 1
        parent_num = row.pop('Next Assembly')
        try:
            flow = self._row_to_flow(row)
        except ValueError:
            print('Value error on row %d' % i)
            raise

        exis = [k for k in self.fg.fragments_with_flow(flow) if k['Source'] == source
                and len([c for c in k.child_flows]) > 0]
        if len(exis) > 0:
            raise DuplicateSubAssembly('(row %d) flow: %s' % (i, flow.link))  # handle this if it comes up

        if parent_num is None:
            return self._new_reference_fragment(flow, Source=source, Row=i)

        else:
            try:
                parent = next(k for k in self.fg.fragments_with_flow(parent_num) if k['Source'] == source)
            except StopIteration:
                print('Bad parent reference: %s; creating new reference fragment' % parent_num)
                return self._new_reference_fragment(flow, Source=source, Row=i)

        self.fg.new_fragment(flow, 'Input', parent=parent, Source=source, Row=i)
        return

    def fragment_from_xl_sheet(self, sheet):
        """
        This function makes the following assumptions:
         - every record corresponds to a distinct fragment
         - every distinct 'Part Number' corresponds to a distinct flow
         - every part-number flow is measured in 'Number of items' and every exchange value is 1.0 item
         - every assembly is unique and none are re-used
        The 'Part Number' is the external reference used to retrieve the flow (which could be a part or an assembly).
        The phrase '<Part Number> ASSEMBLY' is the external reference of the named fragment that produces the flow.
        returns: a top-level fragment.  Every sub-assembly is named after its part number; leaf fragments are unnamed
        and may be duplicated.
        """
        pn = '%s ASSEMBLY' % sheet.name
        if self.fg[pn] is None:
            xl = XlDict(sheet)
            for row in xl.iterrows():
                ref = self._process_row(row, sheet.name)
                if ref is not None:
                    self._refs.append(ref)
        return self.fg[pn]

    def create_assembly(self, assy):
        try:
            sh = next(s for s in self._valid_sheets if s.name == assy)
        except StopIteration:
            print('Assembly not found: %s' % assy)
            return
        return self.fragment_from_xl_sheet(sh)
