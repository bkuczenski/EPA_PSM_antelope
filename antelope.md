# Antelope Catalog

The Antelope Catalog is designed to be a lightweight, low-footprint, python-based tool for interacting with LCA data of all different types, and for using references to these data sources to describe, build, and manipulate foreground models and compute LCIA results.

## Antelope Interface

The driving principle behind the Antelope Catalog is that there is a fixed set of information required to work with LCA data, including performing LCA computations.  I have attempted to design an interface specification that spans the full range of operations, though many more subtle computations (including stochastic simulation) are not yet supported.  The specification includes several distinct interfaces, each of which describes a different sort of information.

The complete interface specification is split into the following parts:

 * Basic (retrieve entities by reference)
 * Index (list and search entities)
 * Inventory (exchange relation and associated queries)
 * Quantity (quantity relation and associated queries, including LCIA)
 * Background (LCI computation)
 * Foreground (fragments and model construction)

The full interface is (mostly) described [here](antelope-interface.md)

## Archives

An [archive](https://github.com/bkuczenski/lca-tools/blob/master/lcatools/archives) is a family of python classes used to store [entities](data-model.md#entities) from the LCA data model.

 * `BasicArchive`s store quantities and flows;
 * `LcArchive`s store quantities, flows, and processes;
 * `LcForeground`s store quantities, flows, and fragments.

Different subclasses of the above classes are used to interpret different types of data sources (e.g. `IlcdArchive`, `EcospoldV2Archive`, `OpenLcaJsonLDArchive`, etc.)  Every archive can implement the [Antelope interface](#antelope-interface).  

## Catalog Resources

Each data resource known to the catalog is defined by a *source*, which is either a path to a local file or a URI; a *reference*, which is a hierarchical signifier intended to express the contents of the resource, and a *data source type*, which refers to the archive subclass used to interpret the source.  Every resource also implements one or more specific interfaces.

## Queries

The Catalog is a query factory.  A query is defined by a particular *origin*, which is a prefix to a semantic reference.  The query object includes all interfaces in its superclass list.  Client code uses the query to access the interfaces, whereupon the catalog relays the request to any resource(s) that are able to answer it (i.e. each resource whose reference matches the query origin and which implements the appropriate interface).

When a query is used to access a specific entity, the query generally returns a Catalog Reference *to* the entity, which encapsulates the query itself.  The catalog reference can then be used to make further queries.

Examples:

    >>> p = cat.query('local.uslci').get('Acetic acid, at plant')
    >>> [k for k in p.inventory()]

this is equivalent to:

    >>> [k for k in cat.query('local.uslci').inventory('Acetic acid, at plant')]

In order to answer the query, the catalog will have to contain a resource whose origin starts with `local.uslci` and which recognizes the term `Acetic acid, at plant` -- the Ecospold V1 version of USLCI can handle this because Ecospold V1 filenames are plain text.

# Links

Please see:
 * [Repository README](README.md)
 * [data-model.md](data-model.md) for a description of the data model
 * [antelope-interface.md](antelope-interface.md) for a semi-complete description of the Antelope interface
 
