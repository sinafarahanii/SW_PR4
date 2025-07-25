import pytest
from unittest.mock import patch
import os
import sys
import subprocess


def test_engine_and_session_are_configured():
    import db
    assert db.engine is not None
    assert db.db_session is not None


@patch("models.Base.metadata.create_all")
def test_init_db_calls_create_all(mock_create_all):
    import db
    mock_create_all.reset_mock()
    db.init_db()
    mock_create_all.assert_called_once_with(bind=db.engine)
