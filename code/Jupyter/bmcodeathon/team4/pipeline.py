import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    max_workers: int

    @property
    def random_state(self):
        return RandomState(self.seed) if self.seed > 0 else None

    @staticmethod
    def get_defaults():
        return {
            'num_queries': 1000,
            'num_results': 200,
            'seed': int(time.time()),               # default seed is random
            'data_path': '/data/pubmed-data.tsv',
            'data_sep': '\t',
            'result_path': '/data/team4/results',
            'hedge_path': '/data/team4/hedges.csv',
            'api_key': None,
            'email': None,
            'rate_limit': 3,
            'max_workers': 1
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


@define
class ResultAtom:
    result_count: int
    return_count: int
    error_count: int
    bias_counts: List[Tuple]


class Pipeline:
    def __init__(self, config: Config, experiment: str = None):
        self.config = config
        self.hedge = None
        self.data = None
        self.experiment = experiment
        if experiment is None:
            experiment = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        self.result_path = Path(self.config.result_path) / experiment
        self.error_count = 0
        self.error_log = None
        self.eutils = EUtils(config.api_key, config.email, config.rate_limit, PREVIEW_PREFIX)

    def load_hedges(self, hedge_path: Optional[str] = None):
        if hedge_path is None:
            hedge_path = self.config.hedge_path
        # TODO: validate expected columns and types?
        return pd.read_csv(hedge_path, index_col='Shortcode')

    def load_data(self, data_path: Optional[str] = None):
        if data_path is None:
            data_path = self.config.data_path
        df = pd.read_csv(data_path, sep=self.config.data_sep)
        # remove rows without query_term
        df = df[df.query_term.notnull()]
        # keep only one copy of each query_term
        df = df.drop_duplicates(subset=['query_term'])
        return df

    def setup(self):
        # prepare the run
        self.hedge = self.load_hedges()
        self.data = self.load_data()

        num_queries = self.config.num_queries
        queries = self.data.sample(num_queries, random_state=self.config.random_state)
        # drop some of the columns to make this tractable
        columns_to_drop = list(set(queries.columns) - {'search_id', 'query_term', 'result_count'})
        self.queries = queries = queries.drop(columns=columns_to_drop)

        # setup the result directoryh
        self.result_path.mkdir()
        self.error_log = (self.result_path / 'error_log.txt').open('w')
        queries_path = self.result_path / 'queries.csv'
        queries.to_csv(queries_path)
        seed_path = self.result_path / 'seed.txt'
        seed_path.write_text(str(self.config.seed))

    # input to the thread pool jobs
    #  - the search_index and sort they are running
    #  - the result_path
    # Work each job does:
    #  - Run the search with that sort order
    #  - Save results to disk
    #  - for each hedge row,
    #      - and the pmid_term into a full query
    #  - the data that we need from each worker will be
    #      - search_index
    #      - sort
    #      - list of hedge and bias_result_count tuples
    def run_case(self, search_index, sort_order):
        query_term = self.queries.query_term[search_index]
        local_error_count = 0

        # that query gets a directory
        query_result_path = self.result_path / str(search_index)
        query_result_path.mkdir(exist_ok=True)
        xml_results = query_result_path / f'{sort_order}.xml'

        # get the query results with relevance
        only_medline = f'({query_term}) AND medline[sb]'
        r = self.eutils.esearch('pubmed', retmax=self.config.num_results, term=only_medline, sort=sort_order)
        xml_results.write_bytes(r.content)
        error_elements = r.xml.xpath('/eSearchResult/ERROR')
        for error in error_elements:
            self.error_count += 1
            local_error_count += 1
            print(f'{search_index}, {sort_order}:\n{error.text}', file=self.error_log)
        pmids = [element.text for element in r.xml.xpath('//IdList/Id')]
        pmid_term = ','.join(pmids) + '[UID]'
        counts = r.xml.xpath('//Count')
        result_count = int(counts[0].text) if len(counts) > 0 else 0
        return_count = len(pmids)

        bias_counts = []
        # for each hedge, run the query against that query_id
        for hedge_name, hedge_row in self.hedge.iterrows():
            hedge_query = hedge_row['Hedge_text']
            full_query = f'{pmid_term} AND ({hedge_query})'
            r = self.eutils.esearch('pubmed', term=full_query, retmax=200)
            error_elements = r.xml.xpath('/eSearchResult/ERROR')
            for error in error_elements:
                self.error_count += 1
                local_error_count += 1
                print(f'{search_index}, {sort_order}, {hedge_name}:\n{error.text}', file=self.error_log)
            bias_result_count = len(r.xml.xpath('//IdList/Id'))
            bias_counts.append((hedge_name, bias_result_count))

        return ResultAtom(result_count, return_count, local_error_count, bias_counts)

    def run(self):
        # start the result file
        output_path = self.result_path / 'results.csv'
        f = open(output_path, 'w')
        writer = csv.writer(f, dialect='unix')
        writer.writerow([
            'search_index',
            'sort',
            'result_count',
            'return_count',
            'error_count',
            'bias_dimension',
            'bias_result_count',
        ])

        # progress bar
        progress = Bar('Runing', max=2*self.config.num_queries)
        stime = time.perf_counter()

        # for each query
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as pool:
            future_to_params = {
                pool.submit(self.run_case, search_index, sort_order): (search_index, sort_order)
                for search_index in self.queries.index
                for sort_order in ['relevance', 'date_desc']
            }
            for future in as_completed(future_to_params):
                progress.next()
                search_index, sort_order = future_to_params[future]
                try:
                    atom = future.result()
                    for hedge_name, bias_result_count in atom.bias_counts:
                        writer.writerow([
                            search_index,
                            sort_order,
                            atom.result_count,
                            atom.return_count,
                            atom.error_count,
                            hedge_name,
                            bias_result_count
                        ])
                except Exception as exc:
                    self.error_count += 1
                    print(f'{search_index}, {sort_order}: exception: {exc}', file=self.error_log)
        progress.finish()
        f.close()
        elapsed = time.perf_counter() - stime
        call_count = self.eutils.call_count
        tput = call_count / elapsed
        print(f'{call_count} API Calls in {elapsed:.2f} seconds ({tput:.1f} per second)')
        print(f'There were {self.error_count} errors')
        print(f'Results in {output_path}')

        return 0
