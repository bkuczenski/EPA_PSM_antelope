# EPA_PSM_Antelope

EPA Product System Modeling Hackathon - antelope branch.  See planning [here](plan.md).

## Overview

The Product Systems being modeled in this project are the landing gear assemblies for an advanced fighter jet.  The model is built from a set of excel spreadsheets that describe the authentic bills of materials for these assemblies in a hierarchical fashion.

I use the disclosure framework outlined in [Disclosure of Product System Models in LCA](https://doi.org/10.1111/jiec.12810) to describe the derived product models in a structured, software-independent format including three lists of entities and three submatrices:

<img alt="Graphical depiction of an LCA disclosure" src="jie-disclosure_fig3.png" width=384>

In the current project, there is no foreground emissions data, so *d-iii* and *d-vi* are blank. Moreover, there is no authentic data on the physical characteristics of the parts, so the numeric values in *d-v* are mocked up.  However, the background terminations (i.e. *d-ii*) are hand-curated to be at least somewhat plausible.

My solution uses the Antelope framework to encode these PSMs as life cycle fragment trees, which are nestable acyclic directed graphs. Each "fragment" is an _observed_ link in a product model, and it functions as a parameterizable exchange.  The disclosures are then generated from traversals of the fragments.

## Components and set-up

The software components used in this entry are contained in two public repositories, and neither is on PyPi because I don't yet know how to use `setuptools`.

 * [lca-tools](https://github.com/bkuczenski/lca-tools), a.k.a. giant antelope pre-release bundle. Please check out `strike-uuids` branch for current work.
 * [lca_disclosures](https://github.com/pjamesjoyce/lca_disclosures). Please check out `typed_flows` branch for current work.

The requirements for these tools are not light:

 - python 3.6+
 - scipy (for background matrix computation-- not strictly needed for this project)
 - pandas (required by `lca_disclosures` for excel output)
 - lxml
 - xlrd
 - requests
 - XlsxWriter
 - python-magic
 - pylzma (though it doesn't work for modern 7z archives, ecoinvent 3.4 and later)

This worked on my system in a new virtualenv.

Future plans include breaking `lca-tools` into several distinct packages:

 - `antelope-interface`, which defines the interface superclasses and has no dependencies
 - `antelope-catalog`, which supports all basic functionality and requires only file I/O packages like lxml and xlrd
 - `antelope-background`, which performs the background matrix construction ([partial ordering](https://doi.org/10.1007/s11367-015-0972-x)) and requires `scipy`. The idea is for this package to be optional, with users instead having the option to use remote resources via Web-based API to perform background computations.

### Installation

For the moment, installation is as follows:

 1. Download `lca-tools` package and install dependencies
 1. Checkout `strike-uuids` branch of `lca-tools`
 1. add `lca-tools` root directory to pythonpath
 1. Download `lca_disclosures` package and symlink to it in the `lca-tools` directory
 1. Checkout `typed_flows` branch of `lca_disclosures
 1. Install and configure `jupyter` if notebook support is desired.

### Configuration and run

The following steps were sufficient on my system:

    $ mkvirtualenv -p /usr/bin/python3.7 hackathon
    (hackathon)$ add2virtualenv /path/to/lca-tools
    (hackathon)$ pip install pandas scipy lxml xlrd XlsxWriter python-magic pylzma requests
    (hackathon)$ cd /path/to/EPA_PSM_hackathon

    [edit user config in gen_disclosures.py]

    (hackathon)$ python gen_disclosures.py

# Documentation

Please see [data-model.md](data-model.md) for a description of the data model and [antelope.md](antelope.md) for a discussion about the features and capabilities of the Antelope interface and Antelope Catalog.


