import sys
from typing import Optional


import pandas as pd
from numpy.random import RandomState
from yaml import safe_load

from .eutils import EUtils

PREVIEW_PREFIX = 'https://eutilspreview.ncbi.nlm.nih.gov/entrez'


class Config:
    def __init__(self,
                 api_key: str,
                 email: str,
                 rate_limit: int,
                 num_queries: int,
                 num_results: int,
                 data_path: str,
                 data_sep: str,
                 result_path: str,
                 hedge_path: str,
                 seed: int):
        self.api_key = api_key
        self.email = email
        self.rate_limit = rate_limit
        self.num_queries = num_queries
        self.num_results = num_results
        self.data_path = data_path
        self.data_sep = data_sep
        self.result_path = result_path
        self.hedge_path = hedge_path
        self.seed = seed

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
            'api_key': '8d4c4f67f2a663e9d0ef6ed4d60a4eedd609',
            'email': 'dansmood@gmail.com',
            'rate_limit': 10
        }

    @staticmethod
    def get_required_keys():
        # TODO: implement a list of required settings that won't be in defaults, like api_key and email
        return set()

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

    @staticmethod
    def get_path():
        return None
        ## The code below is too much for right now - hard code and make the user override
        # if sys.platform == 'win32':
        #     path = os.path.join(os.environ['APPDATA'], 'team4.yaml')
        # else:
        #     path = os.path.join(os.environ['HOME'], '.team4.yaml')
        # return path


class Pipeline:
    def __init__(self, config : Config):
        self.config = config
        self.hedge = None
        self.data = None
        self.eutils = EUtils(config.api_key, config.email, config.rate_limit, PREVIEW_PREFIX)

    def load_hedges(self, hedge_path : Optional[str] = None):
        if hedge_path is None:
            hedge_path = self.config.hedge_path
        # TODO: validate expected columns and types?
        return pd.read_csv(hedge_path)

    def load_data(self, data_path : Optional[str] = None):
        if data_path is None:
            data_path = self.config.data_path
        df = pd.read_csv(data_path, sep=self.data_sep)
        # TODO: remove rows without query
        return df

    def run(self):
        self.hedge = self.load_hedges()
        data = self.load_data()

        num_queries = self.config.num_queries
        self.data = data = data.resample(num_queries, random_state=self.config.random_state)
        print('Not yet implemented', file=sys.stderr)
        return 1
