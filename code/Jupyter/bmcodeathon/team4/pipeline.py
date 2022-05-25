import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from attrs import define
from numpy.random import RandomState
from progress.bar import Bar
from yaml import safe_load

from .eutils import EUtils

PREVIEW_PREFIX = 'https://eutilspreview.ncbi.nlm.nih.gov/entrez'

@define
class Config:
    api_key: Optional[str]
    email: Optional[str]
    rate_limit: int
    num_queries: int
    num_results: int
    data_path: str
    data_sep: str
    result_path: str
    hedge_path: str
    seed: int

    @property
    def random_state(self):
        return RandomState(self.seed) if self.seed > 0 else None

    @staticmethod
    def get_defaults():
        return {
            'num_queries': 1000,
            'num_results': 200,
            'seed': -1,                             # seed below 0 is ignored
            'data_path': '/data/pubmed-data.tsv',
            'data_sep': '\t',
            'result_path': '/data/team4/results',
            'hedge_path': '/data/team4/hedges.csv',
            'api_key': None,
            'email': None,
            'rate_limit': 3
        }

    @classmethod
    def load(cls, path=None):
        cls_kwargs = cls.get_defaults()
        expected_keys = set(cls_kwargs.keys())
        if path is not None:
            with open(str(path)) as f:
                overrides = safe_load(f)
            if any(key not in expected_keys for key in overrides.keys()):
                raise ValueError(f'{path}: invalid setting encountered')
            cls_kwargs.update(overrides)
        return cls(**cls_kwargs)


class Pipeline:
    def __init__(self, config : Config):
        self.config = config
        self.hedge = None
        self.data = None
        self.eutils = EUtils(config.api_key, config.email, config.rate_limit, PREVIEW_PREFIX)

    def load_hedges(self, hedge_path: Optional[str] = None):
        if hedge_path is None:
            hedge_path = self.config.hedge_path
        # TODO: validate expected columns and types?
        return pd.read_csv(hedge_path, index_col='BiasDimension')

    def load_data(self, data_path: Optional[str] = None):
        if data_path is None:
            data_path = self.config.data_path
        df = pd.read_csv(data_path, sep=self.config.data_sep)
        # remove rows without query
        df = df[df.query_term.notnull()]
        return df

    def run(self, result_path=None):
        # prepare the run
        self.hedge = self.load_hedges()
        self.data = self.load_data()

        num_queries = self.config.num_queries
        queries = self.data.sample(num_queries, random_state=self.config.random_state)
        # drop some of the columns to make this tractable
        columns_to_drop = list(set(queries.columns) - {'search_id', 'query_term', 'result_count'})
        self.queries = queries = queries.drop(columns=columns_to_drop)

        # setup the result directory
        if result_path is None:
            result_path = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        result_path = Path(self.config.result_path) / result_path
        result_path.mkdir()
        sample_path = result_path / 'sample_queries.csv'
        queries.to_csv(sample_path, index=False)

        # start the result file
        output_path = result_path / 'results.csv'
        f = open(output_path, 'w')
        writer = csv.writer(f, dialect='unix')
        writer.writerow([
            'search_id',
            'sort',
            'result_count',
            'return_count',
            'bias_dimension',
            'bias_result_count',
        ])

        # progress bar
        progress = Bar('Queries: ', max=self.config.num_queries)
        stime = time.perf_counter()

        # for each query
        eutils = self.eutils
        for _, row in self.queries.iterrows():
            search_id = row['search_id']
            query_term = row['query_term']

            # that query gets a directory
            query_result_path = result_path / search_id
            query_result_path.mkdir()
            relevance_results = query_result_path / 'relevance.xml'
            datedesc_results = query_result_path / 'datedesc.xml'

            # get the query results with relevance
            r = eutils.esearch('pubmed', retmax=self.config.num_results, term=query_term, sort='relevance')
            relevance_results.write_bytes(r.content)
            pmids = [element.text for element in r.xml.xpath('//IdList/Id')]
            result_count = int(r.xml.xpath('//Count')[0].text)
            return_count = len(pmids)

            # post to history server
            r = eutils.epost('pubmed', *pmids)
            webenv = r.webenv
            query_key = r.query_key

            # for each hedge, run the query against that query_id
            for hedge_name, hedge_row in self.hedge.iterrows():
                hedge_query = hedge_row['SearchStrategy']
                r = eutils.esearch('pubmed', term=hedge_query, webenv=webenv, query_key=query_key, retmax=200)
                bias_result_count = len(r.xml.xpath('//IdList/Id'))
                writer.writerow([
                    search_id,
                    'relevance',
                    result_count,
                    return_count,
                    hedge_name,
                    bias_result_count,
                ])

            # save the query results with date descending
            r = eutils.esearch('pubmed', retmax=self.config.num_results, term=query_term, sort='date_desc')
            datedesc_results.write_bytes(r.content)
            pmids = [element.text for element in r.xml.xpath('//IdList/Id')]
            result_count = int(r.xml.xpath('//Count')[0].text)
            return_count = len(pmids)

            # post to history server
            r = eutils.epost('pubmed', *pmids)
            webenv = r.webenv
            query_key = r.query_key

            # for each hedge, run the query against that query_id
            for hedge_name, hedge_row in self.hedge.iterrows():
                hedge_query = hedge_row['SearchStrategy']
                r = eutils.esearch('pubmed', term=hedge_query, webenv=webenv, query_key=query_key, retmax=200)
                bias_result_count = len(r.xml.xpath('//IdList/Id'))
                writer.writerow([
                    search_id,
                    'relevance',
                    result_count,
                    return_count,
                    hedge_name,
                    bias_result_count,
                ])

            progress.next()
        progress.finish()
        f.close()
        elapsed = time.perf_counter() - stime
        tput = eutils.call_count / elapsed
        print(f'{eutils.call_count} API Calls in {elapsed:.2f} seconds ({tput:.1f} per second)')

        return 0
