import pytest

from httpbench.util import format_size, parse_alt_svc_h3_port, parse_size


def test_parse_size_plain_bytes():
    assert parse_size("512") == 512


def test_parse_size_decimal_units():
    assert parse_size("1KB") == 1_000
    assert parse_size("1MB") == 1_000_000
    assert parse_size("1.5GB") == 1_500_000_000


def test_parse_size_binary_units():
    assert parse_size("2MiB") == 2 * 1024 * 1024


def test_parse_size_invalid():
    with pytest.raises(ValueError):
        parse_size("not-a-size")
    with pytest.raises(ValueError):
        parse_size("5XB")


def test_format_size():
    assert format_size(0) == "0B"
    assert format_size(500) == "500B"
    assert format_size(1500) == "1.5KB"
    assert format_size(1_000_000) == "1.0MB"


def test_parse_alt_svc_h3_port():
    header = 'h3=":443"; ma=86400, h3-29=":443"'
    assert parse_alt_svc_h3_port(header) == 443


def test_parse_alt_svc_h3_port_different_port():
    assert parse_alt_svc_h3_port('h3=":4433"; ma=3600') == 4433


def test_parse_alt_svc_h3_port_missing():
    assert parse_alt_svc_h3_port(None) is None
    assert parse_alt_svc_h3_port("") is None
    assert parse_alt_svc_h3_port('h2=":443"') is None
