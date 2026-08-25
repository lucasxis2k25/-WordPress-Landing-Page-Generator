# Mapeamento ABC incremental

O pipeline tem duas fases explícitas:

1. `bootstrap`: lê o workbook de referência uma única vez, captura valores em cache, grava `data/normalized/consolidacao.parquet`, semeia os cadastros mestres e gera os snapshots dourados.
2. `run`: lê somente Parquet e cadastros versionados, processa apenas os produtos indicados, cria uma fila única de pesquisa por cliente + família e só publica depois dos testes dourados.

Execução da primeira etapa:

```text
python -m mapping bootstrap --input input/13_07_26.xlsx --data-dir data --golden-dir tests/golden
python -m mapping run --input data/normalized/consolidacao.parquet --data-dir data --golden-dir tests/golden --products A12038 "VENT. FS/4-400 ET" --incremental --publish-static
```

O comando `run --products all` é bloqueado nesta etapa para impedir o processamento integral antes da aprovação do piloto.
