import json
import os
import redis
import re

# allows to create a Digital Ocean domain record
# on a certain domain only and allows to
# clean up delete it afterwards, and that's it
# stores state in a redis server

DOMAIN = os.environ['DOMAIN']
client = redis.Redis.from_url(os.environ['REDIS_URL'])
domain_records_root = f'/v2/domains/{DOMAIN}/records'


def is_request_allowed(method, path):
    if method == 'POST' and path == domain_records_root:
        return True
    allowed = client.lrange('allowed', 0, -1)
    if not allowed:
        return False
    for allowed_element in allowed:
        try:
            allowed_method, allowed_path = allowed_element.decode('utf-8').split(' ', 1)
        except:
            continue
        if method == allowed_method and path == allowed_path:
            return True
    return False


def response_callback(content: bytes, code, headers):
    data = json.loads(content.decode('utf-8'))

    domain_id = data['domain_record']['id']
    client.lpush('allowed', f'DELETE {domain_records_root}/{domain_id}')  # push an 'allow delete' on that id
