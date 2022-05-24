# pubmed-codeathon-team4
## Introduction 
The bias we are studying comes from differential retrieval. That is, if items pertaining to a given group are less likely to show up in the “top” of a Best Match sorted set, that means that users are less likely to see information pertaining to that group. We will compare results sets returned by Best Match and most recent sorting methods, and compare the items returned for markers of “aboutness” for a given group.

## Installation

This code depends on a number of libraries. To install them from the command-line, execute:

```
pip install -r requirements.txt
```

If you are using a Jupyter nodebook, you can run a bash command using an exclamation point:

```
!pip install -r requirements.txt
```

## Why?

This code manages the Acceptable Usage Limits and makes our search client go as slow as needed.
It will sleep for microseconds if it is out of "tokens" to do an API operation.

This code also manages the search for you so you can concentrate on more interesting things.

## How?

I have no idea how this compares to Biopython, but it works with the E-Utilities test server.
You can import it as follows:

```python
from bmcodeathon.team4 import EUtils, print_element
```

Then, you create an instance of EUtils using the following arguments:
* `apikey` - Your API Key from your PubMed profile
* `email` - Your email address (this is currently unused, but I thought maybe put it in User-Agent.
* `rate` - A numeric, positive rate in requests/second.  This defaults to 3.
* `prefix` - The URL prefix of the server.  This defaults to https://eutils.ncbi.nlm.nih.gov/entrez,
  but you can set it to the test server by passing https://eutilspreview.ncbi.nlm.nih.gov/entrez

For instance:

```python
eutils = EUtils(my_api_key, 'dansmood@gmail.com', 10, 'https://eutilspreview.ncbi.nlm.nih.gov/entrez')
```

The E-Utilities object has methods `einfo`, `esearch`, and `efetch` that return a requests response object.
The response object is decorated with a `xml` method that parses the response as XML.

For example:

```python
r = utils.esearch('pubmed', term='African Americans')
doc = r.xml()
print_element(doc)
```

Since the `doc` above is an XML element, you can use XPath on it:

```python
pmids = [element.text for element in doc.xpath('//IdList/Id')]
print(pmids)
```

These PMIDs can be used with efetch, and "medline" format as well as "xml" is supported:

```python
r = eutils.efetch('pubmed', *pmids)
doc = r.xml()
returned_pmids = [element.text for element in doc.xpath('//PubmedArticle/MedlineCitation/PMID')]
returned_pmids == pmids
```
