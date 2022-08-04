import redis  # import stuff (installed in the venv)

client = redis.Redis()

scope_plugin = ""


def can_use_any_code():
    pass


def is_request_allowed(method, path):
    return True
