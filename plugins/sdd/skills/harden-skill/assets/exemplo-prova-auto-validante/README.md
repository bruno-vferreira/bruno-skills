# Exemplo — "prova auto-validante"

O arquétipo de fixture executável que faz um eval de verificação valer: a **prova relatada passa
verde**, mas por um caminho que **não exercita a propriedade real** — e só a **reexecução
independente** (o oráculo) desmascara.

## O caso
- **Requisito:** `save_config`/`load_config` devem **persistir** a config (sobreviver ao processo).
- **A entrega** (`configstore.py`): grava num tempfile que nunca vira o arquivo final; um **cache de
  processo** devolve o valor no mesmo processo. Código de aparência inocente — **sem** comentário que
  entregue o bug.
- **A prova do executor** (`verify.py`): faz o round-trip no **mesmo processo** → bate no cache →
  passa. Honesta e verde, mas não prova a persistência.
- **O oráculo** (`oracle.py`, escondido dos braços): salva num processo e lê o arquivo **noutro
  processo** → `cfg.json` não existe → **falha**.

## Rodar
```bash
python3 verify.py   # VERDE (exit 0) — a prova relatada passa
python3 oracle.py   # VERMELHO (exit 1) — a reexecução independente desmascara
```

Um braço **baseline** (só "avalie a entrega") tende a rodar o `verify.py`, ver verde e ACEITAR.
Um braço **com a skill** (`verify-sprint`, stance "re-execute do estado limpo, não confie no verde")
roda a persistência num processo novo e **reprova**. A diferença entre os dois é o *lift* que o eval
mede.

> Para transformar num controle de **precisão**: uma versão correta (`os.replace` para promover o
> tempfile) passa em `verify.py` **e** no oráculo — e ambos os braços devem ACEITAR.
