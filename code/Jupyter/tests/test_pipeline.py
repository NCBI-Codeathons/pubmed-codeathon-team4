from bmcodeathon.team4 import Config, Pipeline


def test_just_instantiate():
    config = Config.load()
    pipeline = Pipeline(config)
