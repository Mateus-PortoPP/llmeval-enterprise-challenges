"""Gráficos da replicação (column type annotation, conjunto público adaptado).

Lê SOMENTE o arquivo f1_scores_column_headers.csv gerado por
experiments/enterprise_data_enterprisetables_cta_pub/gather.py. Nenhum número é digitado à mão.

Uso:
    python replicacao_graficos.py [caminho-do-csv] [pasta-de-saida]

Saída (PNG 300 dpi e PDF) na pasta graficos/:
    grafico_f1_com_nomes      F1 ponderado por versão e modelo, com nomes de tabela e colunas
    grafico_f1_sem_nomes      idem, sem nomes
    grafico_queda_sem_nomes   diferença de F1 (com nomes - sem nomes) por versão e modelo
"""
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CSV_PATH = pathlib.Path("experiments/enterprise_data_enterprisetables_cta_pub/f1_scores_column_headers.csv")
OUT_DIR = pathlib.Path("graficos")

# versões na ordem do eixo horizontal
VERSIONS = {
    "c1-large-table-widths": "Tabelas largas",
    "c2-high-sparsity": "Alta esparsidade",
    "c3-low-descriptiveness": "Nomes pouco\ndescritivos",
    "c4-complex-data-types": "Tipos de dados\ncomplexos",
    "all-challenges": "Todas as\ndificuldades",
}

# modelos na ordem das barras: ID (coluna "model" do CSV) -> (nome, cor, rodou com raciocínio?)
# "rodou com raciocínio" = pedido sem temperature 0 e respostas com raciocínio (REPLICACAO.md, desvios D2, D6, D7)
# cores: paleta Okabe-Ito (segura para daltônicos); a mesma cor para o mesmo modelo em todos os gráficos
MODELS = {
    "openai/gpt-4o-2024-08-06": ("GPT-4o (2024-08-06)", "#0072B2", False),
    "openai/gpt-6.1-terra": ("GPT-6.1 Terra", "#E69F00", True),
    "claude-sonnet-5-5": ("Claude Sonnet 5.5", "#56B4E9", True),
    "claude-haiku-5-5": ("Claude Haiku 5.5", "#D55E00", True),
    "claude-fable-5-2": ("Claude Fable 5.2", "#009E73", True),
}
EXTRA_COLORS = ["#CC79A7", "#F0E442", "#999999"]  # para modelos presentes no CSV e não listados acima
REASONING_SUFFIX = " (com raciocínio)"
HATCH = "///"


def load(csv_path: pathlib.Path) -> pd.DataFrame:
    """Devolve uma tabela longa: model, version, header, f1."""
    df = pd.read_csv(csv_path, header=[0, 1, 2], index_col=0)
    rows = []
    for model in df.index:
        for (version, _dataset, header), value in df.loc[model].items():
            rows.append({"model": model, "version": version, "header": header, "f1": value})
    return pd.DataFrame(rows)


def model_styles(models_in_csv: list[str]) -> dict[str, tuple[str, str, bool]]:
    styles = {m: MODELS[m] for m in MODELS.keys() if m in models_in_csv}
    extra = iter(EXTRA_COLORS)
    for m in models_in_csv:
        if m not in styles.keys():
            styles[m] = (m, next(extra), False)
    return styles


def grouped_bars(values: pd.DataFrame, styles: dict, ylabel: str, ylim: tuple[float, float] | None,
                 out_name: str, out_dir: pathlib.Path) -> None:
    """values: índice = versão, colunas = modelo."""
    versions = [v for v in VERSIONS.keys() if v in values.index]
    models = [m for m in styles.keys() if m in values.columns]
    width = 0.8 / len(models)

    fig, ax = plt.subplots(figsize=(12.5, 4.8))
    for ix, model in enumerate(models):
        name, color, reasoning = styles[model]
        xs = [vx - 0.4 + width * (ix + 0.5) for vx in range(len(versions))]
        ys = [values.loc[version, model] for version in versions]
        bars = ax.bar(
            xs, ys, width=width * 0.92, color=color, edgecolor="black", linewidth=0.5,
            hatch=HATCH if reasoning else None, label=name + (REASONING_SUFFIX if reasoning else ""), zorder=3
        )
        for bar, y in zip(bars, ys):
            if pd.isna(y):
                continue
            ax.annotate(
                f"{y:.2f}".replace(".", ","), xy=(bar.get_x() + bar.get_width() / 2, y),
                xytext=(0, 2 if y >= 0 else -2), textcoords="offset points",
                ha="center", va="bottom" if y >= 0 else "top", fontsize=6.5, color="black", zorder=4
            )

    ax.set_xticks(range(len(versions)))
    ax.set_xticklabels([VERSIONS[v] for v in versions], fontsize=9)
    ax.set_ylabel(ylabel, fontsize=10)
    if ylim is not None:
        ax.set_ylim(*ylim)
    else:
        lo, hi = ax.get_ylim()
        pad = 0.08 * (hi - lo)
        ax.set_ylim(lo - (pad if lo < 0 else 0), hi + pad)
        ax.axhline(0, color="black", linewidth=0.8, zorder=2)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=9, title="Modelo",
              title_fontsize=9, alignment="left")

    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{out_name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / f"{out_name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"gerado: {out_dir / out_name}.png e .pdf")


def main() -> None:
    csv_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PATH
    out_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DIR

    df = load(csv_path)
    styles = model_styles(df["model"].unique().tolist())

    with_names = df[df["header"] == "with-headers"].pivot(index="version", columns="model", values="f1")
    without_names = df[df["header"] == "without-headers"].pivot(index="version", columns="model", values="f1")

    grouped_bars(with_names, styles, "F1 ponderado", (0, 1), "grafico_f1_com_nomes", out_dir)
    grouped_bars(without_names, styles, "F1 ponderado", (0, 1), "grafico_f1_sem_nomes", out_dir)
    grouped_bars(with_names - without_names, styles, "Diferença de F1 ponderado\n(com nomes − sem nomes)", None,
                 "grafico_queda_sem_nomes", out_dir)


if __name__ == "__main__":
    main()
