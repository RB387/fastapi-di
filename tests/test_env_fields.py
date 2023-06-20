import os
from dataclasses import dataclass
from unittest import mock

import pytest

from fastapi_di.env_fields import field_str, field_int, field_float, field_bool


@pytest.mark.parametrize(
    "type_hint,field,env,expected_value",
    [
        (str, field_str("URI"), {"URI": "some_uri"}, "some_uri"),
        (int, field_int("PORT"), {"PORT": "1234"}, 1234),
        (float, field_float("DELAY"), {"DELAY": "0.5"}, 0.5),
        (bool, field_bool("FLAG"), {"FLAG": "true"}, True),
        (bool, field_bool("FLAG"), {"FLAG": "false"}, False),
    ],
)
def test_env_fields_success(type_hint, field, env, expected_value):
    @dataclass
    class Config:
        value: type_hint = field

    with mock.patch.dict(os.environ, env):
        config = Config()
        assert config.value == expected_value


@pytest.mark.parametrize(
    "type_hint,field,env,expected_error",
    [
        (int, field_int("PORT"), {"PORT": "notnumber"}, ValueError),
        (float, field_float("DELAY"), {"DELAY": "1,4,"}, ValueError),
        (bool, field_bool("FLAG"), {"FLAG": "1,4,"}, ValueError),
    ],
)
def test_env_fields_parse_error(type_hint, field, env, expected_error):
    @dataclass
    class Config:
        value: type_hint = field

    with mock.patch.dict(os.environ, env):
        with pytest.raises(expected_error):
            Config()


@pytest.mark.parametrize(
    "type_hint,field",
    [
        (str, field_float("URI")),
        (int, field_int("PORT")),
        (float, field_float("DELAY")),
        (bool, field_float("FLAG")),
    ],
)
def test_env_fields_missing_env(type_hint, field):
    @dataclass
    class Config:
        value: type_hint = field

    with mock.patch.dict(os.environ, {}):
        with pytest.raises(ValueError):
            Config()


@pytest.mark.parametrize(
    "type_hint,field,expected_value",
    [
        (str, field_str("URI", default="some_uri"), "some_uri"),
        (int, field_int("PORT", default=1234), 1234),
        (float, field_float("DELAY", default=0.1), 0.1),
        (bool, field_bool("FLAG", default=False), False),
    ],
)
def test_env_fields_missing_env_but_has_default_value(type_hint, field, expected_value):
    @dataclass
    class Config:
        value: type_hint = field

    with mock.patch.dict(os.environ, {}):
        config = Config()
        assert config.value == expected_value
