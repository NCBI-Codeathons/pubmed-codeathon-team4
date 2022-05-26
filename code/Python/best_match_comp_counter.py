#! python3
# You will need to get an API key from NCBI or adjust time.sleep below so that you exceed the unsigned request limits.
# See https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/ for details
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import argparse
import csv
from datetime import datetime
import time
#import calendar
alltests = []
now = datetime.now()

parser = argparse.ArgumentParser(description='''Given a CSV file of test searches, this application retrieves counts for
        the top N of (indexed) Best Match and Date Sorted items when searched against several hedges relating to potentially biased-against groups.
        .''')
parser.add_argument("--searchtermsfile", help="CSV-formatted file of searches to test.")
parser.add_argument("--hedgesfile", help="CSV-formatted file of hedges to test searches against.")
#parser.add_argument("--outputfilestem", help="Stem for name of output file that gets written.")
parser.add_argument("--itemcounts", help="Number of items to pull for each search.")
parser.add_argument("--api_key", help="Api key.")


args = parser.parse_args()
# See note above
apikey = args.api_key

hedges = []
with open(args.hedgesfile, newline='') as hedgecsvfile:
    hedgereader = csv.DictReader(hedgecsvfile)
    for row in hedgereader:
        hedges.append(row)


def getsearch(term, sort, WebEnv=''):
    session = requests.Session()
    retry = Retry(connect=30, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    myurl = "https://eutilspreview.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    payload = {'db': 'pubmed', 'term': term, 'retmax': args.itemcounts, 'retstart': 0, 'usehistory': 'y', 'retmode': 'json', 'email': 'esperr@uga.edu', 'api_key': 'f069cf776feaa627ab9b1e0fc2b090610708', 'sort': sort}
    if WebEnv !='':
        payload['WebEnv'] = WebEnv
    #Adjust accordingly -- we get 50 requests per second now!
    time.sleep(.02)
    r = session.post(myurl, params=payload)
    myjson = r.json()
    return myjson

with open(args.searchtermsfile, newline='') as csvfile:
    termreader = csv.DictReader(csvfile)
    searchcount = 1
    for row in termreader:
        myTest = {}
        myTest['search_count'] = searchcount
        term = row['processed_query'] + " AND 'medline'[Filter]"
        print("\n\nSearch: " + term)
        myTest['search_pointer'] = term[0:5]
        myBMresponse = getsearch(term, "relevance")
        myTest['total_count'] = myBMresponse['esearchresult']['count']
        myBMids = myBMresponse['esearchresult']['idlist']
        myTest['best_match_all'] = myBMids
        myBMidstr = "(" + ' OR '.join(myBMids) + ")"
        myDSresponse = getsearch(term, "date_desc")
        myDSids = myDSresponse['esearchresult']['idlist']
        myTest['date_sort_all'] = myDSids
        myDSidstr = "(" + ' OR '.join(myDSids) + ")"
        searchcount = searchcount + 1

        for hedge in hedges:
            headgestr = "(" + hedge['Hedge_text'] + ")"
            #Constructing a string of PMIDs is the most straightforward thing to do, and should be fine if we use POST
            myBMHedgeIdSearch = myBMidstr + " AND " + headgestr
            myBMidcount = getsearch(myBMHedgeIdSearch, "relevance")
            myTest[hedge['Shortcode'] + '_BM_ids'] = myBMidcount['esearchresult']['idlist']
            myTest[hedge['Shortcode'] + '_BM_count'] = myBMidcount['esearchresult']['count']
            myDSHedgeIdSearch = myDSidstr + " AND " + headgestr
            myDSidcount = getsearch(myDSHedgeIdSearch, "date_desc")
            myTest[hedge['Shortcode'] + '_DS_ids'] = myDSidcount['esearchresult']['idlist']
            myTest[hedge['Shortcode'] + '_DS_count'] = myDSidcount['esearchresult']['count']

        alltests.append(myTest)

#This assumes that the search terms input file ends with '.csv'
myoutputfilestr = "simpleoutput_" + args.searchtermsfile[:-4] + "_" + now.strftime("%Y_%m_%d") + ".csv"
with open(myoutputfilestr, 'w', newline='') as csvfile:
    fieldnames = []
    for key in alltests[0].keys():
        fieldnames.append(key)
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for result in alltests:
        writer.writerow(result)
