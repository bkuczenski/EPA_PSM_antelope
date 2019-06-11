# EPA_PSM_Antelope

EPA Product System Modeling Hackathon - antelope branch.  See planning [here](plan.md).

## Overview

The Product Systems being modeled in this project are the landing gear assemblies for an advanced fighter jet.  The model is built from a set of excel spreadsheets that describe the authentic bills of materials for these assemblies in a hierarchical fashion.

My solution uses the Antelope framework to encode these PSMs as life cycle fragment trees, which are nestable acyclic directed graphs. Each "fragment" is an _observed_ link in a product model, and it functions as a parameterizable exchange.

## Components

### Data Model

Drawing from [Semantic Catalogs for Life Cycle Assessment Data](https://doi.org/10.1016/j.jclepro.2016.07.216), the LCA data model has three distinct entity types:

 * **Flows** are "things in the world" that can be observed and described in quantitative terms.  I regard the unique concept of the flow as the definitive conceptual class of LCA and industrial ecology generally.  In our implementation, every flow must be assigned a specific reference quantity to describe its extent, with the default being "number of items".^1
 * **Quantities** are extensive properties that can be used to describe the extent or dimensionality of specific, observed flows. Mass and price are quantities; LCIA characterizations are also quantities.  
 * **Activities** are interactions of several flows exchanged across a well-defined spatial and temporal boundary.  I use the term "Process" to describe a concrete inventory model  of a specific activity, i.e. an enumeration and quantification of all flows that are co-exchanged across a boundary having a specific spatiotemporal scope.

1- _Note: although the "Semantic Catalogs" article describes flows as having mandatory Compartments, this requirement has been abandoned in favor of contexts.

Additionally, there are ancillary concepts that go along with these primary data types:

 * *Units of measure*.  Several different units can be used to measure the same quantity, and the same unit can also be used to measure different quantities.  For clarity, I like to create distinct indicator units for each distinct quantity.
 * **Contexts** are taken as defined in [Critical review of elementary flows in LCA data](https://doi.org/10.1007/s11367-017-1354-3), namely "...categories typically describing an environmental context of the flow origin or destination ... that include[s] the flow directionality." A context is associated with an _exchange_ and not with a flow entity.
 * *Directions* describe the transit of a flow across a boundary. Directions can have only two values, "Input" and "Output", which can be *most efficiently* represented in python using canonical strings.

### Quantitative Relations

For convenience, clusters of entities can be related together into hybrid objects called "exchanges" and "characterizations":

 * An _exchange_ comprises a process, a flow (with reference quantity), a direction (with respect to the process), and an optional termination (designating the remote end of the exchange, either another process or a context)
 * A _characterization_ comprises a flow (with reference quantity), a characterized quantity, a context, and an optional spatiotemporal scope.

Using these objects, we can define two quantitative relations that collectively describe the full range of computations that occur in life cycle assessment: the _exchange relation_ and the _quantity relation_.  

The exchange relation relates the magnitudes of flows crossing the boundary of an activity.  Given a process (i.e. an inventoried activity) and a designation of that process's reference exchange, the exchange relation computes the magnitude of a given flow (a "query exchange") that is associated with a unit of the reference exchange. The query result is a pure magnitude i.e. a float, which must be interpreted in terms of the given flow's reference quantity.

The quantity relation relates the magnitudes of different quantities ascribed to the same flow or flowable substance.  The quantity relation is best described as mapping a 5-tuple of inputs to a pure magnitude output:




Given a flow and a reference quantity (e.g. mass), the quantity relation computes the magnitude of a  query quantity (e.g. global warming potential over 100 years), the quantity relation computes the 



### Fragment Definition

A fragment has five components:

|Component | Optional? | Data type | Comment|
|---|---|---|---|
|Parent node|Yes|Fragment or `None`|The vantage point from which the exchange is observed|
|Flow|No|Flow entity |The material / service / substance that is observed|
|Direction|No| `Input` or `Output`| with respect to the parent |
|Exchange value|Yes|Float / default 1.0|  Parameterizable|
|Termination|Yes|`None`, `self`, sub-fragment, process, or context|Parameterizable|


### Antelope Catalog

The Antelope Catalog is designed to be a lightweight, low-footprint, python-based tool for interacting with LCA data of all different types, and for using references to these data sources to describe, build, and manipulate foreground models and compute LCIA results.


### Antelope Interface

