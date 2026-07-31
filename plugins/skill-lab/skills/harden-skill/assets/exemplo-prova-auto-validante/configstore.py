import json

_cache = {}


def save_config(path, cfg):
    _cache[path] = dict(cfg)
    with open(path + ".tmp", "w") as f:
        json.dump(cfg, f)


def load_config(path):
    if path in _cache:
        return _cache[path]
    with open(path) as f:
        return json.load(f)
