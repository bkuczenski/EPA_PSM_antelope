import os
from collections import defaultdict

from antelope_catalog.providers.xl_dict import XlDict
from lcatools.interfaces import EntityNotFound
from lcatools.entities.tree_isomorphism import isomorphic, TreeIsomorphismException

from .validation import validate_folder
from .exceptions import DuplicateSubAssembly


class BadParentReference(Exception):
    pass


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

        :param foreground: an Antelope foreground query
        :param folder: [None] directory containing source files
        """
        self._fg = foreground
        self.folder = folder
        for frag in self._fg.fragments():
            self._refs.append(frag)

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

    @property
    def models(self):
        for m in self._refs:
            yield m

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
        try:
            flow = self.fg.get(flow_ref)
        except EntityNotFound:
            flow = self.fg.new_flow(flow_name, 'Number of items', external_ref=flow_ref, **row)
            if self.fg.get(flow_ref) != flow:
                raise KeyError('Flow ref %s failed to properly register' % flow_ref)
        return flow

    def _get_next_name(self, flow):
        """
        This should probably be an interface method, since I already need it again for container building
        Plus, now that fg doesn't support __getitem__ it's a bit awkward
        :param flow:
        :return:
        """
        parent_ref = '%s ASSEMBLY' % flow.external_ref
        try:
            self.fg.get(parent_ref)
        except EntityNotFound:
            return parent_ref
        _ac = 0
        while True:
            parent_ref = '%s ASSEMBLY alt %d' % (flow.external_ref, _ac)
            try:
                self.fg.get(parent_ref)
                _ac += 1
            except EntityNotFound:
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
        qna = row.pop('QNA')
        try:
            amount = float(qna)
        except (TypeError, ValueError):
            amount = 1.0

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
            return self._new_reference_fragment(flow, value=amount, Source=source, Row=i)

        else:
            try:
                parent = next(k for k in self.fg.fragments_with_flow(parent_num) if k['Source'] == source)
            except StopIteration:
                print('Source: %s Row: %d flow: %s' % (source, i, flow))
                raise BadParentReference(parent_num)
                #print('Bad parent reference: %s; creating new reference fragment' % parent_num)
                #return self._new_reference_fragment(flow, value=amount, Source=source, Row=i)

        self.fg.new_fragment(flow, 'Input', parent=parent, value=amount, Source=source, Row=i)
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
        try:
            frag = self.fg.get(pn)
        except EntityNotFound:
            xl = XlDict(sheet)
            for row in xl.iterrows():
                ref = self._process_row(row, sheet.name)
                if ref is not None:
                    self._refs.append(ref)
            frag = self.fg.get(pn)
        return frag

    def create_assembly(self, assy):
        try:
            sh = next(s for s in self._valid_sheets if s.name == assy)
        except StopIteration:
            print('Assembly not found: %s' % assy)
            return
        return self.fragment_from_xl_sheet(sh)

    '''
    Detect and remove duplicates
    '''

    def duplicate_subassemblies(self):
        """
        Generates sets of foreground fragments with the same flow and direction- in the present application these are
        duplicated subassemblies.  Only reports the highest-level subassemblies that are duplicated (i.e. fragments
        whose parents are non-duplicated).  Computes sequentially and feeds from a local dict to avoid "dict changed
        size during iteration"
        :return:
        """
        dupes = set()
        top_dupes = defaultdict(set)

        # first, make a list of all duplicated non-leaf fragments
        for flow in self.fg.flows():
            for dirn in ('Input', 'Output'):
                asm = set(k for k in self.fg.fragments_with_flow(flow, direction=dirn) if k.term.is_fg)
                if len(asm) > 1:
                    dupes |= asm

        # next, screen them down to top-level frags (frags whose parents are nonduplicated)
        for frag in dupes:
            if frag.reference_entity not in dupes:
                top_dupes[frag.flow, frag.direction].add(frag)

        # finally, generate the duplicate sets
        for v in top_dupes.values():
            yield v

    def _split_subassembly(self, frag):
        parent_ref = self._get_next_name(frag.flow)
        self.fg.split_subfragment(frag)
        self.fg.name_fragment(frag, parent_ref)
        self._refs.append(frag)

    def reduce_duplicates(self, master, *dupes, verify=True):
        """

        :param master:
        :param dupes: 0 or more fragments that are duplicates
        :param verify: [True] whether to test that the master and duplicate are isomorphic
        :return:
        """
        if master.reference_entity is not None:
            self._split_subassembly(master)
        for dupe in dupes:
            if verify:
                try:
                    isomorphic(master, dupe)
                except TreeIsomorphismException:
                    print('Fragment %s failed isomorphism' % dupe)
                    continue
            ditch = self.fg.split_subfragment(dupe, replacement=master)
            self.fg.delete_fragment(ditch)
