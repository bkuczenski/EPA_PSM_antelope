# EPA_PSM_antelope
Working space for EPA Product System Modeling Hackathon - antelope branch

## Outlook 2019-12-01

Reviewed C Mutel's [perdu](https://github.com/cmutel/perdu) package and also took a look at [wurst](https://github.com/IndEcol/wurst).  They don't really jibe with me for some reason... re-read the THEMIS paper though and that is some intense stuff.  I think the problem is that I reject the notion of bundling everything into a giant matrix.  I basically reject the integrated hybrid proposal as being falsely closed, or rather, providing a technical closure that is essentially superficial and papers over the spectacular inaccuracy that it normalizes.

My notional solution, ever inchoate, is to pull the foreground out and have it live on its own, with a universe of background systems to link against for scenario analysis.  It doesn't really solve any problem, just points to an inadequacy in the "all-in" system model approach that is in evidence with THEMIS and MRIO more generally.

The point of this writeup isn't to provide an un-thought-through, off-the-cuff defense of the hopeless (un-thought-through, off-the-cuff) Antelope framework- instead it is to establish a set of tasks for iterating Antelope tools within the framework of the SEDRP hackathon.

### New Product Systems

The agonist for this task is the set of new product systems that have been provided: namely the CCD MRF and the PCB assembly.  Taking those one at a time, the CCD MRF model is a single process with-- crucially-- some terminated flows and some cutoffs, which are rendered as terminated to intermediate contexts.  We need to think about those terminate-to-context ones for a minute, because that smells like an opportunity, but the terminated flows show exactly the deficiencies of the OLCA product system and the promise of the fragment model.  On the other hand, the fragment model doesn't really do anything: it's not going to get any smaller than the already existing OLCA archive, and in the absence of any tools to work with the unlinked fragment model it is no different from an unlinked OLCA archive.

Thinking back to the context aspect, though: it is easy to imagine an intermediate context being an automatic map-to-background.  I forget where this could fit in but it certainly could.

The PCB dataset on the other hand... should be an easy run.  EXCEPT... between June and now I have apparently changed the API for fg.get() to return None instead of raising EntityNotFound.  That is a serious party foul right there WTF.  During code review I have utterly convinced myself that it should raise an error.  (fixes)

Anyway, the PCB system more or less builds, with two exceptions:
 * The code required that Part Number be not blank (modified to fallback to Part Name)
 * The code expected the spreadsheet name to be the same as the part name, but in the PCB case the spreadsheet is simply named 'BOM'.

For this second problem, the reliance on the spreadsheet name comes from the fact that there are multiple parts... for now I will modify it to simply try the sheet name, and if not found, try the first row name after that, and (continue to) use the first row name canonically.

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
