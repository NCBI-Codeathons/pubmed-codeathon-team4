# pubmed-codeathon-team4
## Introduction
This was done as part of the NCBI Virtual Codeathon: Investigating Accurate and Equitable Representation in PubMed Search Results. Our team decided to look at differences in how likely results were to show up in the first page of search results when sorted by “Best Match”. We compared result sets returned by Best Match and date-sorted results returned by recently published and compared the results for markers of “aboutness” for any given group

## Table of Contents 
1. [Methods]
2. [Process]

## Methods 
We compared results sets returned by Best Match and most recent sorting methods, and compared the items returned for markers of “aboutness” for a given group. We selected five axes of intersectionality of vulnerable populations: race/ethnicity, women, gender minorities, geographic bias, and geriatric and tried to determine if results returned by Best Match were biased for/against these given populations. 

## Installation
This code depends on a number of libraries. To install them from the command-line, execute:
pip install -r requirements.txt
 
If you are using a Jupyter nodebook, you can run a bash command using an exclamation point:
!pip install -r requirements.txt

## Why?
This code manages the Acceptable Usage Limits and makes our search client go as slow as needed. It will sleep for microseconds if it is out of "tokens" to do an API operation.
I like that the response doesn't hide that the response is XML - you can use XPath naturally rather than using Python specific constructions.
It also is growing to integrate with the history server, but this needs to be better described.

## How to Instantiate
I have no idea how this compares to Biopython, but it works with the E-Utilities test server. You can import it as follows:
from bmcodeathon.team4 import EUtils, print_element
Then, you create an instance of EUtils using the following arguments:
- apikey - Your API Key from your PubMed profile
- email - Your email address (this is currently unused, but I thought maybe put it in User-Agent.
- rate - A numeric, positive rate in requests/second. This defaults to 3.
- prefix - The URL prefix of the server. This defaults to https://eutils.ncbi.nlm.nih.gov/entrez, but you can set it to the test server by passing https://eutilspreview.ncbi.nlm.nih.gov/entrez
For instance:
eutils = EUtils(my_api_key, my_email, 10, 'https://eutilspreview.ncbi.nlm.nih.gov/entrez')
The E-Utilities object has methods einfo, esearch, efetch, and epost that return a requests response object. The response object is decorated with a xml attribute that holds the response as XML. This has been changed to only use XML to integrate with the history server

## Basic Usage 
For example:
r = eutils.esearch('pubmed', term='African Americans', retmax=200)
print_element(r.xml)
Since the r.xml above is an XML element, you can use XPath on it:
pmids = [element.text for element in r.xml.xpath('//IdList/Id')]
print(pmids)
These PMIDs can be used with efetch, and "medline" format as well as "xml" is supported:
r = eutils.efetch('pubmed', *pmids)
doc = r.xml()
returned_pmids = [element.text for element in doc.xpath('//PubmedArticle/MedlineCitation/PMID')]
returned_pmids == pmids

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

## With History Server 
See E-Utilities and the History Server for what we are trying to do. Do a search with history:
r = eutils.esearch('pubmed', term='African Americans', sort='relevance', retmax=200)
print(r.webenv)
print(r.query_key)
Post those 200 results as a new saved result set:
pmids = [element.text for element in r.xml.xpath('//IdList/Id')]
r2 = eutils.post('pubmed', *pmids, webenv=r.webenv)
print_element(r2.xml)
Compose the existing search with a new search:
r3 = eutils.esearch('pubmed', term='Hedge query', webenv=r2.webenv, query_key=r2.query_key, retmax=200)
print_element(r3.xml)

## References 
