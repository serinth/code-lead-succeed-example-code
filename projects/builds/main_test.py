import pytest
from projects.builds.src.main import test_main
from models.test import test_bigquery_model
def test_main_thing():
    assert test_main() == test_bigquery_model()