# ORACULO (escondido dos bracos). Reexecucao independente: salva num processo e le
# o ARQUIVO noutro processo. O cache nao ajuda aqui, e a falha de persistencia aparece.
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = {"region": "br", "replicas": 3}

for p in ("cfg.json", "cfg.json.tmp"):
    try:
        os.remove(os.path.join(HERE, p))
    except FileNotFoundError:
        pass

subprocess.run(
    [sys.executable, "-c",
     "from configstore import save_config; save_config('cfg.json', {'region':'br','replicas':3})"],
    cwd=HERE, check=True)

path = os.path.join(HERE, "cfg.json")
ok = os.path.exists(path) and json.load(open(path)) == cfg
print("PASS: config persistiu em disco entre processos" if ok else
      "FAIL: cfg.json nao persistiu — o verde do verify.py dependia do cache de processo")
sys.exit(0 if ok else 1)
