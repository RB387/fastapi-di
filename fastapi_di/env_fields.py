import os
from dataclasses import field
from typing import Any, Callable

MISSING = object()


def env_var_factory(env_var: str, cast_fn: Callable = str, default: Any = MISSING):
    def factory():
        val = os.getenv(env_var, default=default)
        if val is MISSING:
            raise ValueError(f"Env variable {env_var} is not specified")

        return cast_fn(val)

    return factory


def env_field(env_var: str, cast_fn: Callable = str, **kwargs):
    default = kwargs.pop("default", MISSING)

    return field(
        default_factory=env_var_factory(env_var, cast_fn=cast_fn, default=default),
        **kwargs,
    )


def field_str(env_var: str, **kwargs):
    return env_field(env_var, str, **kwargs)


def field_int(env_var: str, **kwargs):
    return env_field(env_var, int, **kwargs)


def field_float(env_var: str, **kwargs):
    return env_field(env_var, float, **kwargs)


def _bool(val: str | bool) -> bool:
    if isinstance(val, bool):
        return val

    if val.lower() in ("true", "1"):
        return True
    elif val.lower() in ("false", "0"):
        return False

    raise ValueError(f"Cannot case value {val} to bool")


def field_bool(env_var: str, **kwargs):
    return env_field(env_var, _bool, **kwargs)
