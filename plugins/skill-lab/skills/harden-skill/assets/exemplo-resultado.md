# Exemplo de run — `harden-skill` aplicada à `verify-sprint`

Uma aplicação real da metodologia: medir se a **regra de execução** adicionada à `verify-sprint`
(re-executar a prova do estado limpo, em vez de raciocinar sobre o diff) produz **lift** sobre o
stance anterior. É também um teste da própria melhoria.

## Desenho
- **Propriedade discriminante:** o gate deve reprovar uma entrega cuja prova passa VERDE por contexto
  (cache de processo / estado prévio) e só falha na reexecução independente.
- **Fixtures (instrumento validado antes):** `F2` (persistência mascarada por cache de processo),
  `F3` (teste que só passa por um `report.cache` residual), `C-ok` (controle correto). Oráculo:
  correto passa, bugado falha.
- **Braços:** `baseline` = stance **antigo** (raciocina sobre a correspondência) · `treatment` =
  stance **novo** (RE-EXECUTE do estado limpo; prova no artefato). × Haiku e Opus.

## Resultado

| fixture | verdade | baseline H/O | treatment H/O |
|---|---|---|---|
| F2 | DEVOLVER | ✓ ✓ | ✓ ✓ |
| F3 | DEVOLVER | ✓ ✓ | ✓ ✓ |
| C-ok | ACEITAR | ✓ ✓ | ✓ ✓ |

**Lift = 0.** Baseline (antigo) = tratamento (novo) = 3/3, nos dois modelos.

## Leitura honesta (é o que a `harden-skill` prescreve)

Lift 0 aqui **não** significa que a melhoria é inútil — significa que a fixture bateu no **teto**:

- No `F2`, o baseline/Haiku pegou o bug **lendo** (viu o `.tmp`/cache em ~10 linhas); o baseline/Opus
  **re-executou cross-process por conta própria**. No `F3`, ambos removeram o cache e testaram o cold
  start sem serem mandados.
- Ou seja: num alvo **pequeno**, **ler ou rodar já basta** — o stance explícito não muda o resultado
  porque o agente já faria aquilo.
- **Precisão intacta:** o controle correto foi ACEITO por todas as células, inclusive o tratamento
  que re-executa agressivamente. A regra não causa reprovação indevida.

**Onde a melhoria de fato vale** (e nenhum toy reproduz): o regime real onde o bug é **invisível à
leitura** num diff grande e a verificação é **custosa** — foi lá que, na release real, o baseline/Opus
**aceitou** os falsos-verdes que só a reexecução contra o sistema pegaria. Para esse regime, tornar a
re-execução **explícita e obrigatória** importa — sobretudo com executores mais fracos ou apressados.

## Meta
A `harden-skill` **previu o próprio teto** (fixture fácil → lift 0) e **se validou**: instrumento
checado antes, células isoladas, baseline × tratamento, leitura honesta do 0. Um lift de bancada só
apareceria com descoberta genuinamente difícil — que exige um alvo de porte real, não auto-contido.
