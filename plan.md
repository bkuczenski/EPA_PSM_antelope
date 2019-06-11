# EPA_PSM_antelope
Working space for EPA Product System Modeling Hackathon - antelope branch

## Task description

The foreground model consists of two distinct product systems, for main and front landing gear for a high-performance fighter jet.  The models are provided as excel spreadsheets. The task is to convert the spreadsheets into LCA-capable models, ultimately loading them into OLCA, and linking them to LCI data sources to construct meaningful LCI models.

Background data to be used includes: USLCI, USEEIO, Ecoinvent, ELCD.  There is also an electricity LCI model but that is not really relevant because the foreground model does not include any electricity demand.

We also want to import the LCI models into OLCA, at least if we decide that a python shell is inadequate to the task of demonstrating the model.  

## Plan Of Attack

Antelope framework is well suited for this: fragments are essentially equivalent to the spreadsheet definition provided.

(using master, since ContextRefactor is not quite finished) We will:

 1. read spreadsheets into fragments
 1. enumerate cutoffs and ensure the correct number and set of cutoffs
 1. create a minimal interface for finding terminations based on material description
 1. manually identify terminations in the several background sources
 1. terminate with scenarios, including necessary flow characterization information as needed (piece to mass, piece to volume, piece to value)
 1. adapt M Srocka's import tool
 1. implement USEEIO in antelope (maybe we do want to finish ContextRefactor after all)
 1. write documentation.

If that comes in under 60 hours I will be shocked.
