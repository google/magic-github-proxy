import os

from magicproxy import proxy


def test_cleans_custom_queries():
    proxy.queries_to_clean(['key'])
    path = 'https://github.com/orthros?key=123212'
    actual = proxy._clean_path_queries(path)
    assert actual == 'https://github.com/orthros?'
    

def test_cleans_repeated_custom_queries():
    proxy.queries_to_clean(['key'])
    path = 'https://github.com/orthros?key=123212&key=asdf%0ss'
    actual = proxy._clean_path_queries(path)
    assert actual == 'https://github.com/orthros?'

def test_cleans_bare_queries():
    proxy.queries_to_clean(['key'])
    path = 'https://github.com/orthros?key='
    actual = proxy._clean_path_queries(path)
    assert actual == 'https://github.com/orthros?'

def test_cleans_repeated_bare_custom_queries():
    proxy.queries_to_clean(['key'])
    path = 'https://github.com/orthros?key=&key='
    actual = proxy._clean_path_queries(path)
    assert actual == 'https://github.com/orthros?'

def test_cleans_trailing_queries():
    proxy.queries_to_clean(['key'])
    path = 'https://github.com/orthros?someval=&key=123212'
    actual = proxy._clean_path_queries(path)
    assert actual == 'https://github.com/orthros?someval=&'

def test_leaves_queries_alone_if_not_set():
    proxy._query_params_to_clean = []
    path = 'https://github.com/orthros?someval=&key=123212'
    actual = proxy._clean_path_queries(path)
    assert actual == 'https://github.com/orthros?someval=&key=123212'