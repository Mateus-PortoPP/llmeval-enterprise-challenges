#!/bin/bash
# Replicação parcial do experimento de CTA (enterprisetables_cta_pub) com as tabelas publicadas no zip.
# NÃO executa o preprocess.py (que regeneraria as tabelas chamando o GPT-4o).
#
# Uso:
#   bash replicacao_rodar.sh <etapa> <nome-curto> <id-do-modelo> <api_name> [prefixo-do-exp_name]
#
#   etapa:   instances | prepare | execute | parse | evaluate | all (prepare+execute+parse+evaluate)
#   prefixo: padrão "enterprise-data-enterprisetables-cta-pub" (formato dos autores)
#
# Requer: venv ativado, PYTHONPATH=./, chaves carregadas (set -a; source .env; set +a) e a variável
# REPLICACAO_ZIP_DIR apontando para a pasta "adapted-sportstables-cta" descompactada (só na etapa instances).

set -e

stage="$1"
short="$2"
model="$3"
api_name="$4"
prefix="${5:-enterprise-data-enterprisetables-cta-pub}"

dataset="enterprisetables_cta_pub"
versions=(c1-large-table-widths c2-high-sparsity c3-low-descriptiveness c4-complex-data-types all-challenges)
exp_root="data/column_type_annotation/${dataset}/experiments"

run_stage() {  # $1 = etapa, demais = argumentos hydra
  local st="$1"; shift
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] ${st}: $*"
  case "$st" in
    prepare)  python tasks/column_type_annotation/prepare_requests.py "$@" ;;
    # a confirmação de custo do código original ("press enter to continue") é respondida pelo `yes ""`
    execute)  yes "" | python tasks/execute_requests.py -cp "../config/column_type_annotation" "$@" ;;
    parse)    python tasks/column_type_annotation/parse_responses.py "$@" ;;
    evaluate) python tasks/column_type_annotation/evaluate.py "$@" ;;
  esac
}

for version in "${versions[@]}"; do
  for headers in with-headers without-headers; do
    exp_name="${prefix}_${short}_${version}_${headers}"

    if [ "$stage" = "instances" ]; then
      mkdir -p "${exp_root}/${exp_name}"
      rm -rf "${exp_root}/${exp_name}/instances"
      cp -R "${REPLICACAO_ZIP_DIR}/${version}" "${exp_root}/${exp_name}/instances"
      echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] instances: ${exp_name}"
      continue
    fi

    args=(
      exp_name="$exp_name"
      dataset="$dataset"
      api_name="$api_name"
      model="$model"
      use_inst_all_column_types=false
      max_tokens_over_ground_truth=null
    )
    if [ "$headers" = "without-headers" ]; then
      args+=(linearize_table.csv_params.header=false 'linearize_table.template="{{table}}"')
    fi

    if [ "$stage" = "all" ]; then
      for st in prepare execute parse evaluate; do run_stage "$st" "${args[@]}"; done
    else
      run_stage "$stage" "${args[@]}"
    fi
  done
done
