#!/bin/bash
# Rodada completa de um modelo (execute, parse, evaluate), com nova tentativa automática se uma etapa cair
# (por exemplo, por falha de conexão). Respostas já recebidas ficam no cache e não são pedidas de novo.
#
# Uso: bash replicacao_rodada.sh <nome-curto> <id-do-modelo> <api_name> [prefixo] [sufixo-do-log]
#   Para uma execução repetida (cache separado): REPLICACAO_OPENAI_CACHE_DIR=openai_cache_rep2 bash replicacao_rodada.sh
#     <nome-curto> <id> <api> repeticao2 rep2
#   (o prefixo "repeticao2" não é lido pelo gather.py; as pastas precisam ter instances/ e requests/ copiados da rodada 1)

short="$1"; model="$2"; api_name="$3"
prefix="${4:-enterprise-data-enterprisetables-cta-pub}"
tag="${5:-}"
max_tries=6

for st in execute parse evaluate; do
  try=1
  while true; do
    log="logs_replicacao/completa_${st}_${short}${tag:+_$tag}$([ $try -gt 1 ] && echo "_tentativa${try}").log"
    bash replicacao_rodar.sh "$st" "$short" "$model" "$api_name" "$prefix" > "$log" 2>&1 && break
    echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] etapa ${st} falhou na tentativa ${try} (log: ${log})"
    try=$((try + 1))
    [ $try -gt $max_tries ] && { echo "desistindo após ${max_tries} tentativas"; exit 1; }
    sleep 30
  done
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] etapa ${st} concluída (tentativas: ${try})"
done
