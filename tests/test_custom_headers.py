import os

from magicproxy import proxy

def test_clean_request_headers_strips_custom_headers():
    proxy.custom_reqeust_headers_to_clean(['X-Custom-Me'])
    headers = dict()
    headers['X-Custom-Me'] = 'A Custom Value'
    actual = proxy._clean_request_headers(headers)
    assert 'X-Custom-Me' not in actual

def test_strips_custom_headers():
    proxy.custom_reqeust_headers_to_clean(['X-Custom-Me'])
    headers = dict()
    headers['X-Custom-Me'] = 'A Custom Value'
    actual = proxy._clean_custom_request_headers(headers)
    assert 'X-Custom-Me' not in actual

def test_leaves_headers_alone_if_undefined():
    proxy._custom_request_headers_to_clean = []
    headers = dict()
    headers['X-Custom-Me'] = 'A Custom Value'
    actual = proxy._clean_custom_request_headers(headers)
    assert headers == actual