# Antelope Interface Specification

The Antelope Interface is an abstraction layer between a foreground modeling setting and an LCA data source.  The interface is meant to supply access to all information that would be required to utilize a data resource.  The ultimate goal is to create a Web API implementation of the interface that would enable practitioners to perform LCA without requiring physical access to any data source or computational capabilities, other than foreground model traversal.  This will enable light-weight (incl. web-based) tools for LCA model construction and critical review, as well as mediated and/or privacy-preserving access to proprietary resources.

### Basic Interface

The [Basic Interface](https://github.com/bkuczenski/lca-tools/blob/strike-uuids/lcatools/interfaces/abstract_query.py) provides elementary access to a resource:

 * `get(external_ref)` - retrieve an entity by its reference
 * `get_item(external_ref, item)` - retrieve a property of an entity

### Index Interface

The [Index Interface](https://github.com/bkuczenski/lca-tools/blob/strike-uuids/lcatools/interfaces/iindex.py) describes the contents and metadata of specific data sources.  The interface includes:

 * `processes(...)`, `flows(...)`, `quantities(...)`, `contexts(...)`, `flowables(...)` - list / search among entities
 * `count(entity_type)` - return the number of a given entity type
 * `synonyms(term)` - return known synonyms for a given term, where the term signifies a flowable, context, or quantity
 * `lcia_methods(...)` - quantities that have an `Indicator` property
 * `unmatched_flows(flows)` - given a list of flow terms, return a list of terms that are not known synonyms
 * `terminate(flow, ...)` - given a flow, return a list of processes that include it as a reference exchange

The index interface cannot retrieve any quantitative information.

### Inventory Interface

The [Inventory Interface](https://github.com/bkuczenski/lca-tools/blob/strike-uuids/lcatools/interfaces/iinventory.py) implements the exchange relation and provides all information about exchanges and process inventories.

 * `exchanges(process_ref, ...)` - list exchanges, without values
 * `exchange_values(process_ref, flow_ref, ...)` - list exchanges, with values, for a given process, having a given flow
 * `inventory(process, ...)` - return a full list of exchanges with values
 * `exchange_relation(...)` - compute the exchange relation
 * `lcia(...)` - compute foreground LCIA of a process's direct emissions (requires a quantity interface for the supplied lcia method)
 * `traverse(fragment)`, `fragment_lcia(fragment)` -- probably belong in the foreground interface.

### Quantity Interface

The [Quantity Interface](https://github.com/bkuczenski/lca-tools/blob/strike-uuids/lcatools/interfaces/iquantity.py)
implements the quantity relation and handles all manner of flow-property conversions and LCIA.

 * `get_canonical(term)` - returns the canonical version of a given quantity (i.e. several different resources may have their own concept of "mass" but the catalog has only one canonical mass)
 * `profile(flow, ...)` - return a list of known characterizations for a given flow or flowable
 * `characterize(...)` - assign a characterization value to a flow-quantity pair
 * `factors(quantity, ...)` - return a list of known characterization factors for a given quantity
 * `cf(flow, quantity)` - compute the quantity relation and return a float, or 0.0
 * `quantity_relation(...)` - compute the quantity relation and return a data structure that describes the value and provenance of the result
 * `do_lcia(quantity, inventory, ....)` - Given a quantity and an iterable of exchanges, generate and return an `LciaResult` object

### Background Interface

The [Background Interface](https://github.com/bkuczenski/lca-tools/blob/strike-uuids/lcatools/interfaces/ibackground.py) handles all information involving ordering and inversion of a technology matrix.  There are two implementations of the background interface.  The first (trivial) implementation simply assumes reported inventories *are* computed LCI results. It performs no ordering nor LCI computation.

The second implementation requires index and inventory access to a resource,  computes a partial ordering of all process/reference flow pairs in the resource, constructs and inverts a technology matrix, and stores the results for static computation.  Monte Carlo simulations are not currently supported.

 * `check_bg()` - triggers the construction of the technology matrix
 * `foreground_flows(...)` - lists and searches process/flow pairs that are not required by the background
 * `background_flows(...)` - lists and searches process/flow pairs that are included in the background
 * `exterior_flows(...)` - lists and searches flow/context pairs that are not included in the reference exchanges for any processes in the resource
 * `cutoffs(...)` - exterior flows whose context is non-elementary
 * `consumers(process, ref_flow)` - lists process/flow pairs that list the supplied process/flow pair as a dependency
 * `dependencies(process, ref_flow)` - lists foreground and background requirements of the supplied process/flow pair
 * `emissions(process, ref_flow)` - lists exterior flows associated with the supplied process/flow pair
 * `foreground(process, ref_flow)` - returns an ordered list of exchanges in the foreground that are encountered in a traversal of the matrix beginning at the supplied process/flow pair, and ending upon interaction with the background.
 * `is_in_background(process, ref_flow)` - bool
 * `ad(process, ref_flow)`, `bf(process, ref_flow)` - return ad_tilde or bf_tilde for the supplied process/flow pair
 * `lci(process, ref_flow)` - compute the aggregated LCI result for the process/flow pair
 * `bg_lcia(process, quantity, ref_flow, ...)` - equivalent to `quantity.do_lcia(process.lci(ref_flow))`

### Foreground Interface

The [Foreground Interface](https://github.com/bkuczenski/lca-tools/blob/strike-uuids/lcatools/interfaces/iforeground.py) is used to construct foreground models (which do not include processes by definition).  Most operations dealing with foreground construction are performed on fragment entities directly, and not over the interface.

The foreground interface is still under development.  

 * `new_flow(name, ref_quantity, ...)` - create a flow.  The default ref_quantity is "Number of items".
 * `new_fragment(flow, direction, ....)` - create a fragment.
 * `fragments()` - list and search fragments
 * `name_fragment(fragment, name)` - assign a new external ref to a fragment
 * `fragments_with_flow(flow, ...)` - generate fragments that contain a given flow
 
More to come.

# Links

Please see:
 * [Repository README](README.md)
 * [data-model.md](data-model.md) for a description of the data model
 * [antelope.md](antelope.md) for a discussion about the features and capabilities of the Antelope interface and Antelope Catalog
 
