#!/bin/bash
# Teste-piloto: executa só as 5 primeiras tabelas (na ordem usada pelo pipeline: 0, 1, 10, 11, 12) de cada versão.
#
# Os 5 pedidos são COPIADOS dos pedidos já preparados da rodada completa (mesmo exemplo sorteado, mesmas linhas),
# de modo que as respostas ficam no cache e são reaproveitadas na rodada completa, sem custo duplicado.
# Os experimentos do piloto usam o prefixo "piloto5", que o gather.py ignora.
#
# Uso: bash replicacao_piloto.sh <nome-curto> <id-do-modelo> <api_name>
# Requer que `bash replicacao_rodar.sh instances ...` e `bash replicacao_rodar.sh prepare ...` já tenham rodado.

set -e

short="$1"
model="$2"
api_name="$3"

full_prefix="enterprise-data-enterprisetables-cta-pub"
pilot_prefix="piloto5"
exp_root="data/column_type_annotation/enterprisetables_cta_pub/experiments"
versions=(c1-large-table-widths c2-high-sparsity c3-low-descriptiveness c4-complex-data-types all-challenges)
tables=(0 1 10 11 12)

for version in "${versions[@]}"; do
  for headers in with-headers without-headers; do
    full="${exp_root}/${full_prefix}_${short}_${version}_${headers}"
    pilot="${exp_root}/${pilot_prefix}_${short}_${version}_${headers}"
    rm -rf "$pilot"
    mkdir -p "$pilot/instances" "$pilot/requests"
    cp "$full/instances/all_column_types.json" "$pilot/instances/"
    for t in "${tables[@]}"; do
      cp -R "$full/instances/$t" "$pilot/instances/$t"
      cp "$full/requests/$t.json" "$pilot/requests/$t.json"
    done
  done
done

for stage in execute parse evaluate; do
  bash replicacao_rodar.sh "$stage" "$short" "$model" "$api_name" "$pilot_prefix"
done
