# Classify using MeSH terms

## Others
 
https://www.ncbi.nlm.nih.gov/mesh?term=Health+Status+Disparities


## Identify Descriptors for Health Disparities

Health disparity, Minority, and Vulnerable Populations has tree number "M01.270"

There are some tree numbers and descriptors under "M01" persons that may be of interest as well.

The following MeSH RDF SPARQL query returns the identifiers and URIs of Descriptors under "M01.270".
The descritpor URI is included only so that it can be run in the User interface query tool.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
PREFIX mesh: <http://id.nlm.nih.gov/mesh/>
PREFIX mesh2022: <http://id.nlm.nih.gov/mesh/2022/>
PREFIX mesh2021: <http://id.nlm.nih.gov/mesh/2021/>
PREFIX mesh2020: <http://id.nlm.nih.gov/mesh/2020/>

SELECT ?desc ?desc_id ?desc_label ?tn_label
FROM <http://id.nlm.nih.gov/mesh>
WHERE { 
  ?tn a meshv:TreeNumber .
  ?tn rdfs:label ?tn_label .
  ?desc a meshv:TopicalDescriptor .
  ?desc meshv:treeNumber ?tn .
  ?desc rdfs:label ?desc_label .
  ?desc meshv:identifier ?desc_id .
  FILTER(STRSTARTS(?tn_label, "M01.270")) .
}
```

## Determine entry terms for each

