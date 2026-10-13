# benchmark

Medição de abertura e memória contra Helium, Thorium, Chrome e ungoogled. Resultados em [BASELINE](../BASELINE.md); gráficos em `docs/img/bench/`.

- `bench/ab.py`: orquestra rodadas intercaladas (uma chamada do harness por navegador por volta, ordem rotacionada, gate load1 < 1). Não edita `bench/harness.py`.
- `bench/charts.py`: resume os `jsonl` copiados (mediana, IC95 por bootstrap, razão pareada vs Helium) e gera SVG sem dependências; `--from-json docs/img/bench/v02.json` redesenha sem os dados brutos.
- `bench/pss_proc.py`: PSS por processo (anon/arquivo/shmem) com 10 abas.
- Regra: nenhuma métrica mais de 2% pior que o Helium. Perfil `performance`, máquina ociosa, nada de Cezanne.

## resumo para agentes

Rode `bench/ab.py` por bloco (`warm`, `tabs`, `first`), depois `bench/charts.py`; atualize o README (bloco de gráficos no topo) e `docs/BASELINE.md`. Compare PSS separando a 1ª execução do perfil (alta) da 2ª.
