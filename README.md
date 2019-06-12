# EPA_PSM_Antelope

EPA Product System Modeling Hackathon - antelope branch.  See planning [here](plan.md).

## Overview

The Product Systems being modeled in this project are the landing gear assemblies for an advanced fighter jet.  The model is built from a set of excel spreadsheets that describe the authentic bills of materials for these assemblies in a hierarchical fashion.

My solution uses the Antelope framework to encode these PSMs as life cycle fragment trees, which are nestable acyclic directed graphs. Each "fragment" is an _observed_ link in a product model, and it functions as a parameterizable exchange.

## Components and set-up

The software components used in this entry are contained in two public repositories, and neither is on PyPi because I don't yet know how to use `setuptools`.

 * [lca-tools](https://github.com/bkuczenski/lca-tools), a.k.a. giant antelope pre-release bundle. Please check out `strike-uuids` branch for current work.
 * [lca_disclosures](https://github.com/pjamesjoyce/lca_disclosures). Please check out `typed_flows` branch for current work.

The requirements for these tools are fairly extensive:

 - python 3.6
 - scipy (for background matrix computation)
 - pandas (required by `lca_disclosures`)
 - lxml
 - xlrd
 - XlsxWriter
 - pylzma, if direct access to 7z archives is desired
 - six (though python2 is probably not supported)
 - perhaps others. I will update this after testing.

Future plans include breaking `lca-tools` into several distinct packages:

 - `antelope-interface`, which defines the interface superclasses and has no dependencies
 - `antelope-catalog`, which supports all basic functionality and requires only file I/O packages like lxml and xlrd
 - `antelope-background`, which performs the background matrix construction ([partial ordering](https://doi.org/10.1007/s11367-015-0972-x)) and requires `scipy`

For the moment, installation is as follows:

 1. Download `lca-tools` package and install dependencies
 1. Checkout `strike-uuids` branch of `lca-tools`
 1. add `lca-tools` root directory to pythonpath
 1. Download `lca_disclosures` package and symlink to it in the `lca-tools` directory
 1. Checkout `typed_flows` branch of `lca_disclosures
 1. Install and configure `jupyter` if notebook support is required.
 

### Data Model

Drawing from [Semantic Catalogs for Life Cycle Assessment Data](https://doi.org/10.1016/j.jclepro.2016.07.216), the LCA data model has three distinct entity types:

 * **Flows** are "things in the world" that can be observed and described in quantitative terms.  I regard the unique concept of the flow as the definitive conceptual class of LCA and industrial ecology generally.  In our implementation, every flow must be assigned a specific reference quantity to describe its extent, with the default being "number of items".<sup>1</sup>
 * **Quantities** are extensive properties that can be used to describe the extent or dimensionality of specific, observed flows. Mass and price are quantities; LCIA characterizations are also quantities.  
 * **Activities** are interactions of several flows exchanged across a well-defined spatial and temporal boundary.  I use the term "Process" to describe a concrete inventory model  of a specific activity, i.e. an enumeration and quantification of all flows that are co-exchanged across a boundary having a specific spatiotemporal scope.

1- *Note: although the "Semantic Catalogs" article describes flows as having mandatory Compartments, this requirement has been abandoned in favor of contexts.*

Additionally, there are ancillary concepts that go along with these primary data types:

 * *Units of measure*.  Several different units can be used to measure the same quantity, and the same unit can also be used to measure different quantities.  A unit is simply a string, and can indicate a measurement but is insufficient to identify a quantity. For clarity, I like to create distinct indicator units for each quantity.
 * **Contexts** are as defined in [Critical review of elementary flows in LCA data](https://doi.org/10.1007/s11367-017-1354-3), namely "...categories typically describing an environmental context of the flow origin or destination ... that include[s] the flow directionality."  An exclusive nomenclature of Contexts (but including synonyms) is integral to LCIA; however, each data source is free to natively define any contexts, which can then be harmonized with the LCIA engine.  A context is always associated with an _exchange_ and not with a flow entity.  Similarlly, there is no such thing as an "elementary flow", only an elementary exchange.
 * *Directions* describe the transit of a flow across a boundary. Directions can have only two values, "Input" and "Output", which can be *most efficiently* represented in python using canonical strings.

### Quantitative Relations

For convenience, clusters of entities can be related together into hybrid objects called "exchanges" and "characterizations":

 * An _exchange_ comprises a process, a flow (with reference quantity), a direction (with respect to the process), and an optional termination (designating the remote end of the exchange, either another process or a context)
 * A _characterization_ comprises a flow (with reference quantity), a characterized quantity, a context (with an inherent direction), and an optional spatiotemporal scope.

Using these objects, we can define the two quantitative relations that collectively describe the full range of computations that occur in life cycle assessment, the _exchange relation_ and the _quantity relation_:

 * Given an exchange, the exchange relation is the magnitude of the exchanged flow (in terms of its reference quantity) that is associated with a unit of a specified reference flow;

 * Given a characterization, the quantity relation is the magnitude of the characterized quantity that is equivalent to a unit of the characterized flow's reference quantity.

Both relations map _n_-tuples of entities to real numbers.  The exchange relation is used to compute the values of nonzero entries in the _A_ and _B_ matrices; the quantity relation is used for unit conversions and to compute the values of nonzero entries in the _C_ matrix.


### Fragment Definition

A fragment can be thought of as a parameterized foreground exchange. It has five components:

|Component | Optional? | Data type | Comment|
|---|---|---|---|
|Parent node|Yes|Fragment or `None`|The vantage point from which the exchange is observed|
|Flow|No|Flow entity |The material / service / substance that is observed|
|Direction|No| `Input` or `Output`| with respect to the parent |
|Exchange value|Yes|Float / default 1.0|  Parameterizable|
|Termination|Yes|`None`, `self`, sub-fragment, process, or context|Parameterizable|

A collection of fragments is well-defined if every fragment's parent node is either None or in the collection.  Such a collection forms a [forest](https://en.wikipedia.org/wiki/Tree_(graph_theory)#Forest), and every fragment with None parent is called a "reference fragment".  The set of reference fragments equals the distinct set of product systems modeled by the forest.

### Antelope Catalog

The Antelope Catalog is designed to be a lightweight, low-footprint, python-based tool for interacting with LCA data of all different types, and for using references to these data sources to describe, build, and manipulate foreground models and compute LCIA results.


### Antelope Interface

