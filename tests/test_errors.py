import pytest
import oneai
from tests.constants import URL_INPUT


pipeline = oneai.Pipeline([oneai.skills.Anonymize()])


def test_api_key_error():
    api_key = oneai.api_key
    oneai.api_key = None
    with pytest.raises(oneai.exceptions.APIKeyError):
        pipeline.run("test")
    oneai.api_key = api_key


def test_input_error():
    with pytest.raises(oneai.exceptions.InputError):
        pipeline.run(URL_INPUT)  # no HtmlToArticle Skill, should fail


def test_server_error():
    with pytest.raises(oneai.exceptions.ServerError):
        pipeline.run(oneai.Input("https://this-url-is-fake.fake"))
