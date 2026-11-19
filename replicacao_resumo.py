"""Resumo por execução: F1 ponderado, erros, tokens de entrada/saída, custo e blocos de raciocínio.

Lê apenas os arquivos gerados pelo pipeline (responses/ e results/) de cada experimento.

Uso:
    python replicacao_resumo.py [prefixo] [arquivo-de-saida.csv]

    prefixo: "enterprise-data-enterprisetables-cta-pub" (padrão, rodada completa) ou "piloto5" (teste-piloto)
"""
import pathlib
import sys

import pandas as pd

from llms4de.data import get_task_dir, load_json
from llms4de.model import _anthropic, _openai


def summarize(exp_dir: pathlib.Path) -> dict:
    _, short, version, headers = exp_dir.name.split("_")
    row = {"modelo": short, "versao": version, "cabecalho": headers}

    n = n_ok = n_thinking = n_not_stop = 0
    tok_in = tok_out = tok_reasoning = 0
    cost = cost_reported = 0.0
    max_in = 0
    served_models, providers, stop_reasons = set(), set(), set()
    for path in sorted((exp_dir / "responses").glob("*.json")):
        response = load_json(path)
        n += 1
        if "choices" in response.keys():  # OpenAI format (OpenRouter)
            n_ok += 1
            usage = response["usage"]
            r = _openai._Response(response)
            this_in = usage["prompt_tokens"]
            tok_in += this_in
            tok_out += usage["completion_tokens"]  # includes reasoning tokens
            reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
            tok_reasoning += reasoning
            if reasoning > 0 or response["choices"][0]["message"].get("reasoning"):
                n_thinking += 1
            cost += r.total_cost()
            if usage.get("cost") is not None:
                cost_reported += usage["cost"]
            served_models.add(response.get("model"))
            providers.add(response.get("provider"))
            stop = response["choices"][0]["finish_reason"]
        elif response.get("type") == "message":  # Anthropic format
            n_ok += 1
            usage = response["usage"]
            r = _anthropic._Response(response)
            this_in = r.input_usage()
            tok_in += this_in
            tok_out += usage["output_tokens"]  # includes thinking tokens
            if any(block["type"] in ("thinking", "redacted_thinking") for block in response["content"]):
                n_thinking += 1
            cost += r.total_cost()
            served_models.add(response.get("model"))
            stop = response["stop_reason"]
        else:  # failed request
            continue
        max_in = max(max_in, this_in)
        stop_reasons.add(stop)
        if stop not in ("stop", "end_turn", "stop_sequence"):
            n_not_stop += 1

    row["respostas"] = n
    row["respostas_ok_api"] = n_ok
    row["respostas_com_raciocinio"] = n_thinking
    row["respostas_nao_terminadas_normalmente"] = n_not_stop
    row["tokens_entrada"] = tok_in
    row["tokens_saida"] = tok_out
    row["tokens_raciocinio_informados"] = tok_reasoning
    row["max_tokens_entrada_por_pedido"] = max_in
    row["custo_calculado_usd"] = round(cost, 6)
    row["custo_informado_api_usd"] = round(cost_reported, 6)
    row["modelo_que_respondeu"] = ";".join(sorted(map(str, served_models)))
    row["provedor"] = ";".join(sorted(map(str, providers - {None})))
    row["stop_reasons"] = ";".join(sorted(map(str, stop_reasons)))

    results = exp_dir / "results"
    if (results / "classification_report.json").is_file():
        row["f1_ponderado"] = load_json(results / "classification_report.json")["weighted avg"]["f1-score"]
        errors = load_json(results / "errors.json")
        row["erros"] = sum(v for k, v in errors.items() if k not in ("null", None))
        row["erros_detalhe"] = str({k: v for k, v in errors.items() if k not in ("null", None)})
    return row


def main() -> None:
    prefix = sys.argv[1] if len(sys.argv) > 1 else "enterprise-data-enterprisetables-cta-pub"
    out = sys.argv[2] if len(sys.argv) > 2 else None
    exp_root = get_task_dir("column_type_annotation") / "enterprisetables_cta_pub" / "experiments"
    exp_dirs = sorted(p for p in exp_root.glob(f"{prefix}_*/") if (p / "responses").is_dir())
    df = pd.DataFrame([summarize(p) for p in exp_dirs])
    if len(df.index) == 0:
        print("nenhuma execução encontrada")
        return
    pd.set_option("display.width", 250, "display.max_columns", 50, "display.max_rows", 500)
    print(df.to_string(index=False))
    print()
    totals = df.groupby("modelo")[["respostas", "respostas_ok_api", "respostas_com_raciocinio", "tokens_entrada",
                                   "tokens_saida", "custo_calculado_usd", "custo_informado_api_usd"]].sum()
    print(totals.to_string())
    if out is not None:
        df.to_csv(out, index=False)


if __name__ == "__main__":
    main()
