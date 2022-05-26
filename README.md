# pubmed-codeathon-team4
## Introduction
This was done as part of the NCBI Virtual Codeathon: Investigating Accurate and Equitable Representation in PubMed Search Results. Our team decided to look at differences in how likely results were to show up in the first page of search results when sorted by “Best Match”. We compared result sets returned by Best Match and date-sorted results returned by recently published and compared the results for markers of “aboutness” for any given group

## Table of Contents 
1. [Methods]
2. [Process]

## Methods 
We compared results sets returned by Best Match and most recent sorting methods, and compared the items returned for markers of “aboutness” for a given group. We selected five axes of intersectionality of vulnerable populations: race/ethnicity, women, gender minorities, geographic bias, and geriatric and tried to determine if results returned by Best Match were biased for/against these given populations. 

## Process
Load pubmed-data.tsv
Remove rows where the query is NULL
Sample Nq queries from the set
For each query:
  - Come up with a query ID - UUID() or sequential
  - Run the query through esearch with both date ordered and relevance ordered, repeating the following steps:
  - Run the search with the sort
  - Save the top results (XML) for accountability
  - Post the top Nr results to the history server
  - And each query against those results on the history server, getting a count of results

### Example Workflows
Run first seed search and grab first N Best Match results
1. Run that same seed search using Date Sort and grab first N results
2. Search the PMIDs from set 1 against hedge 1
3. Run the PMIDs from set 2 against hedge 1
4. Repeat steps 3 and 4 for each remaining hedge
5. Return to step 1 with the next seed search

### Pipeline Steps 
Data preparation/setup
- Load pubmed-data.tsv into a pandas dataframe
- Drop the rows where the query_term column is null
- Deduplicate the rows keeping only the first row containing a non-unique query_term
- Initialize a random number generator to a seed specified in configuration file or the UNIX epoch, e.g. int(time.time())
- Sample N queries (taken from configuration file) from the query data.
- Drop all columns except search_id, query_term, and number of results
- Save that as a CSV - queries.csv
- Start an error log - error_log.txt
- Save the seed - seed.txt
- Initialize a threadpool with 5 workers (configurable, but 5 is enough)
Running the pipeline
- For each query in the sampled queries and each sort (relevance, date_desc), do the following steps:
- - Build a query combining the query_term AND medline[sb]
- - Do an esearch returning 200 results
- - Save the results either to one or the other file - search_index/relevance.xml
- - Pull out the pmids and build a new query over those AND each hedge
- Its the work above that is run by the threadpool.

## Output
For each query, we will have the following data from stage 1:
- A query id
- The query string
- Count of results (overall - same with relevance or date order)
- BiasDimension
- RelevanceResults - path or set of PMIDS
- DateDescResults - path or set of PMIDS
- Top N - always 200
- BiasDimenson
- RelevanceCount
- DateDescCount
For used search hedges see hedges,csv in the data folder. 

##References 
