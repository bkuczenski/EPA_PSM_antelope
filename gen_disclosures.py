from antelope_epa import PsmTerminationBuilder, create_annotated_foreground, create_epa_psms, mock_inventory_data
from antelope_catalog import LcCatalog
from lca_disclosures.antelope import AntelopeTraversalDisclosure

ANNOTATION_FILE = 'PSM-hackathon-leaf-flows_annotated.xlsx'  # in working directory

###############################################################################################
### TODO: User-editable config begins here
###############################################################################################
DATA_DIR = '/data/GitHub/2019/LCAproductsystemassembly_1/data-foreground/'
OUTPUT_DIR = 'output'
CATALOG_DIR = '/data/LCI/hack2it'
ELCD_PATH = '/data/LCI/ELCD/ELCD3.2-a.zip'  # set None to download it
###############################################################################################
### End User-editable config
###############################################################################################

import os


def load_background_data_sources(cat, elcd=False, elcd_source=None):
    """
    Downloads and installs USLCI, USEEIO, and ELCD databases into an Antelope catalog.

    :param cat: LcCatalog
    :param elcd: [False] whether to load ELCD 3.2 database
    :param elcd_source: [None] path to local ELCD 3.2 file, if present locally, to avoid 117 MB download
    :return:
    """

    us_ref = 'local.uslci.olca'

    if us_ref not in cat.references:
        # USLCI config is included in antelope repo by default (via dropbox download)
        from antelope_catalog.data_sources.local import make_config
        us = make_config('uslci')

        for res in us.make_resources(us_ref):
            cat.add_resource(res)

    cat.query(us_ref).check_bg()

    # USEEIO can be downloaded from data.gov
    useeio_ref = 'local.usepa.useeio.1.1'
    if useeio_ref not in cat.references:
        cat.new_resource(useeio_ref, None, 'OpenLcaJsonLdArchive',
                         interfaces=('inventory', 'quantity'), static=False,
                         download={'url': 'https://pasteur.epa.gov/uploads/10.23719/1375574/USEEIOv1.1-JSONLD-foropenlca.zip',
                                   'md5sum': 'dda25b5f25fe4112e592029373525773'},
                         config={'hints': [('context', 'air', 'to air'), ('context', 'water', 'to water')]})
    cat.query(useeio_ref).check_bg()

    usd = next(cat.query(useeio_ref).quantities(Name='price'))
    assert usd.uuid == 'b0682037-e878-4be4-a63a-a7a81053a691'

    if elcd:
        elcd_ref = 'local.elcd.3.2'
        if elcd_ref not in cat.references:
            # ELCD can be downloaded via dropbox but I haven't done local cfg yet. Warning; 117MB.
            # escape the download by providing elcd_source filename that points to an ILCD archive (zipped or unzipped)
            cat.new_resource(elcd_ref, elcd_source, 'IlcdLcia',
                             interfaces=('inventory', 'quantity', 'background'), static=False,
                             download={'url': 'https://www.dropbox.com/s/annfy0ngvpp5m3d/ELCD3.2-a.zip?dl=1',
                                       'md5sum': 'be9c8cd2796e0699ef6fd524935b1c51'})
        cat.index_ref(elcd_ref)  # -- done in bg generation for other resources


def simple_product_model_disclosures(cat, fg_name, termination_file, psm='74A400800-1001 ASSEMBLY', quiet=True,
                                     folder=OUTPUT_DIR):
    """
    Creates a set of disclosures describing the simplest product model, 74A400800-1001 Retract Actuator assembly.
    Demonstrates the use of the PsmTerminationBuilder class to build a container fragment (whose child flows are
    populated by cutoffs from interior subfragments), and to terminate cutoff fragments by scenario.

    The disclosure is generated from a traversal of a fragment according to a scenario (or set of scenarios).  One
    key parameter in the traversal is whether to "descend" into sub-fragments, treating them as part of the parent
    fragment, or to treat them as distinct fragments ("non-descend").  The non-descend option reveals some additional
    information, because the linkages between the subfragment and the parent must be made explicit in the disclosure.

    This function creates four disclosures of the same product model:
     - container fragment terminated to USLCI, descend
     - container fragment terminated to USEEIO, descend
     - container fragment terminated to USLCI, non-descend
     - leaf nodes terminated to USLCI (descend is not relevant because container fragment doesn't do anything)

    :param cat:
    :param fg_name:
    :param termination_file:
    :param psm:
    :param quiet:
    :param folder:
    :return:
    """

    fg = cat.foreground(fg_name, reset=True)
    simple_frag = fg.get(psm)

    builder = PsmTerminationBuilder(cat, fg, termination_file, sheet='terminations')

    builder.terminate_leaf_nodes(simple_frag, 'local.uslci.olca', scenario='breakout uslci')

    container_frag = builder.build_container(simple_frag, 'local.uslci.olca', 'local.usepa.useeio.1.1')

    print('Generating Disclosures for simple product model:\n%s\n' % simple_frag)

    print('Descend into subfragments; USLCI termination')
    d = AntelopeTraversalDisclosure(container_frag.traverse('local.uslci.olca'), quiet=quiet, folder_path=folder)
    d.write_excel('simple_uslci_descend')

    print('Descend into subfragments; USEEIO termination')
    d = AntelopeTraversalDisclosure(container_frag.traverse('local.usepa.useeio.1.1'), quiet=quiet, folder_path=folder)
    d.write_excel('simple_useeio_descend')

    print('Non-Descend subfragments; USLCI termination')
    container_frag.term.descend = False
    d = AntelopeTraversalDisclosure(container_frag.traverse('local.uslci.olca'), quiet=quiet, folder_path=folder)
    d.write_excel('simple_uslci_nondescend')

    print('Terminated leaf nodes: USLCI termination')
    container_frag.term.descend = True
    d = AntelopeTraversalDisclosure(container_frag.traverse('breakout uslci'), quiet=quiet, folder_path=folder)
    d.write_excel('simple_uslci_termed')


def large_product_model_mixed_scenarios(cat, fg_name, termination_file, psm='74A400500-1017 ASSEMBLY', quiet=True,
                                        folder=OUTPUT_DIR):
    """
    Demonstrates the disclosure framework for a larger fragment.  Here we are building a container fragment just as
    before, and terminating it to both USLCI and USEEIO.  But we are also terminating the fragment's leaf nodes
    to ELCD, which is incompletely described, so many flows are left un-terminated.

    When we traverse the fragment using one scenario (either USLCI or USEEIO) we see the container fragment handling
    all the unterminated flows from the subfragments.  When we traverse the fragment using just ELCD, we see a lot of
    cutoffs that are not handled at all.  When we traverse the fragment using a mixture of ELCD and the US data, we
    see the terminated leaf nodes going to the ELCD process, and the container fragment picking up the leftovers.

    This function creates four disclosures of the same product model:
     - leaf nodes partially terminated to ELCD
     - container fragment terminated to USEEIO (USLCI is similar)
     - Combined USEEIO and ELCD scenarios, descend
     - Combined USEEIO and ELCD scenarios, non-descend

    :param cat:
    :param fg_name:
    :param termination_file:
    :param psm:
    :param quiet:
    :param folder:
    :return:
    """

    fg = cat.foreground(fg_name, reset=True)  # reset causes reload from
    large_frag = fg.get(psm)

    builder = PsmTerminationBuilder(cat, fg, termination_file, sheet='terminations')

    builder.terminate_leaf_nodes(large_frag, 'local.elcd.3.2', 'ELCD')

    container_frag = builder.build_container(large_frag, 'local.usepa.useeio.1.1')

    print('Generating Disclosures for large product model:\n%s\n' % large_frag)

    print('Leaf terminations: ELCD')
    d = AntelopeTraversalDisclosure(container_frag.traverse('ELCD'), quiet=quiet, folder_path=folder)
    d.write_excel('large_elcd_termed')

    print('Container terminations: USEEIO')
    d = AntelopeTraversalDisclosure(container_frag.traverse('local.usepa.useeio.1.1'), quiet=quiet, folder_path=folder)
    d.write_excel('large_useeio_container')

    print('Mixed scenarios, descend')
    d = AntelopeTraversalDisclosure(container_frag.traverse(('local.usepa.useeio.1.1', 'ELCD')), quiet=quiet,
                                    folder_path=folder)
    d.write_excel('large_mixed_descend')

    print('Mixed scenarios, nondescend')
    container_frag.term.descend = False
    d = AntelopeTraversalDisclosure(container_frag.traverse(('local.usepa.useeio.1.1', 'ELCD')), quiet=quiet,
                                    folder_path=folder)
    d.write_excel('large_mixed_nondescend')


def do_epa_study(cat_dir=CATALOG_DIR, elcd=True, elcd_source=ELCD_PATH, fg_name='psm-hackathon',
                 scratch=False):
    # create and prepare the catalog
    cat = LcCatalog(cat_dir)
    load_background_data_sources(cat, elcd=elcd, elcd_source=elcd_source)

    # create and prepare the foreground
    fg = create_annotated_foreground(cat, fg_name, ANNOTATION_FILE, scratch=scratch)
    create_epa_psms(fg, DATA_DIR)

    # generate mock price + mass data
    price = cat.query('local.usepa.useeio').get('b0682037-e878-4be4-a63a-a7a81053a691')
    cf_file = os.path.join(cat_dir, fg_name, 'cfs.json')
    mock_inventory_data(fg, price, ANNOTATION_FILE, save_file=cf_file)

    # generate disclosures
    simple_product_model_disclosures(cat, fg_name, ANNOTATION_FILE)
    large_product_model_mixed_scenarios(cat, fg_name, ANNOTATION_FILE)


if __name__ == '__main__':
    do_epa_study(scratch=True)
