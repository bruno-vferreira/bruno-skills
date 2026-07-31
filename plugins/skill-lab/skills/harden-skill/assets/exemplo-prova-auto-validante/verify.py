from configstore import save_config, load_config

cfg = {"region": "br", "replicas": 3}
save_config("cfg.json", cfg)
assert load_config("cfg.json") == cfg
print("OK")
