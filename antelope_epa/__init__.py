from .epa_psm_antelope import EpaF18Foreground
from .inventory_data import MockCfGenerator
from .terminations import PsmTerminationBuilder


def create_annotated_foreground(cat, fg_name, annotation_file, scratch=False):
    """
    Create / retrieve the foreground with the specified name. Load the annotation file and apply annotations to the
    flows.
    :param cat:
    :param fg_name:
    :param annotation_file:
    :param scratch: [False] whether to start from scratch
    :return:
    """
    do_save = False
    fg = cat.foreground(fg_name, delete=scratch)
    if fg.count('flow') < 810:
        # load annotations
        ar = cat.get_archive(fg.origin)

        from lcatools.entities.xlsx_editor import XlsxArchiveUpdater

        with XlsxArchiveUpdater(ar, annotation_file) as x:
            x.apply()

        f = ar['3M1169C3D6A']
        do_save = True
    else:
        f = fg.get('3M1169C3D6A')
    assert f.has_property('Material')
    assert f['Material'] == 'Nickel'  # unit test - mid-op

    assert len([k for k in fg.flows(Material='.')]) == 810

    if do_save:
        fg.save()
    return fg


def create_epa_psms(fg, data_dir):
    """
    Use the custom FG-handling class to generate fragments from the Excel files provided.  The procedure has two major
    steps:
     0- validate the spreadsheets in the data folder
     1- create an assembly from each valid sheet
     2- reduce duplicate subassemblies, splitting each one off into its own reference fragment

    :param fg:
    :param data_dir:
    :return:
    """

    efg = EpaF18Foreground(fg, folder=data_dir)
    if len([k for k in efg.models]) == 27:
        return True

    for sheet in efg.valid_sheets:
        efg.create_assembly(sheet)

    assert len([k for k in efg.models]) == 8
    assert efg.fg.count('fragment') == 1528

    for dup in efg.duplicate_subassemblies():
        sdup = sorted(dup, key=lambda x: not x.is_reference)  # make sure
        efg.reduce_duplicates(*sdup)

    assert len([k for k in efg.models]) == 27
    assert efg.fg.count('fragment') == 1402
    assert len([k for k in efg.duplicate_subassemblies()]) == 0

    efg.fg.save()

    return True


def mock_inventory_data(fg, price, inventory_file, **kwargs):
    """
    Use a spreadsheet annotated with mock material / mass / price information to generate mass and price
    characterizations for leaf flows
    :param fg: foreground query
    :param price: economic quantity used for price data (canonical mass is used)
    :param inventory_file:
    :return:
    """
    # two required quantity inputs to the mock generator
    mass = fg.get_canonical('mass')

    mock = MockCfGenerator(mass, price, inventory_file, sheet='mass_hints', **kwargs)

    f = fg.get('NAS6203-4D')  # pick a part at random to demo the characterization
    mock.characterize(f, demo=True)

    for f in fg.flows(Material='.'):  # regexp: matches any material spec
        mock.characterize(f, demo=False)

    fg.save()
    mock.save()
