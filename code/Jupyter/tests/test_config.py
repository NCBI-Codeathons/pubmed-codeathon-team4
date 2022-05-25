from textwrap import dedent
import numpy as np

import pytest

from bmcodeathon.team4 import Config


def test_defaults():
    config = Config.load()
    assert config.rate_limit == 10
    assert config.random_state is None


def test_with_overrides(tmp_path):
    data = dedent("""\
        rate_limit: 20
        seed: 222918
    """)
    path = tmp_path / 'team4.yaml'
    path.write_text(data)

    config = Config.load(path)

    assert config.rate_limit == 20
    assert isinstance(config.random_state, np.random.RandomState)


def test_unknown_setting_error(tmp_path):
    data = dedent("""\
        unknown: 20
    """)
    path = tmp_path / 'team4.yaml'
    path.write_text(data)

    with pytest.raises(ValueError):
        Config.load(path)

#
# Python's typing doesn't enforce type hints - moving on
#
# def test_invalid_type_error(tmp_path):
#     data = dedent("""\
#         rate_limit: '/data/some_file.txt'
#     """)
#     path = tmp_path / 'team4.yaml'
#     path.write_text(data)
#
#     with pytest.raises(ValueError):
#         config = Config.load(path)
