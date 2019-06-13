from .epa_psm_antelope import EpaF18Foreground
from .inventory_data import MockCfGenerator
from .terminations import PsmTerminationBuilder


def create_annotated_foreground(cat, fg_name, annotation_file):
    fg = cat.create_foreground(fg_name)

    # load annotations
    ar = cat.get_archive(fg.origin)

    from lcatools.entities.xlsx_editor import XlsxArchiveUpdater

    with XlsxArchiveUpdater(ar, annotation_file) as x:
        x.apply()

    f = ar['3M1169C3D6A']
    assert f.has_property('Material')
    assert f['Material'] == 'Nickel'

    assert len([k for k in fg.flows(Material='.')]) == 810

    fg.save()
    return fg


def create_epa_psms(fg, data_dir):

    efg = EpaF18Foreground(fg, folder=data_dir)
    if len([k for k in efg.models]) == 27:
        return True

    for sheet in efg.valid_sheets:
        efg.create_assembly(sheet)

    assert len([k for k in efg.models]) == 8
    assert efg.fg.count('fragment') == 1528

    for dup in efg.duplicate_subassemblies():
        sdup = sorted(dup, key=lambda x: not x.is_reference)
        efg.reduce_duplicates(*sdup)

    assert len([k for k in efg.models]) == 27
    assert efg.fg.count('fragment') == 1402
    assert len([k for k in efg.duplicate_subassemblies()]) == 0

    efg.fg.save()

    return True


def mock_inventory_data(cat, fg, inventory_file, **kwargs):
    """
    Use a spreadsheet annotated with mock material / mass / price information to generate mass and price
    characterizations for leaf flows
    :param cat:
    :param fg_name:
    :param inventory_file:
    :return:
    """
    f = fg.get('NAS6203-4D')

    mass = fg.get_canonical('mass')
    price = cat.query('local.usepa.useeio').get('b0682037-e878-4be4-a63a-a7a81053a691')

    mock = MockCfGenerator(mass, price, inventory_file, sheet='mass_hints', **kwargs)
    mock.characterize(f, demo=True)

    for f in fg.flows(Material='.'):  # regexp: matches any material spec
        mock.characterize(f, demo=False)

    fg.save()
    mock.save()
