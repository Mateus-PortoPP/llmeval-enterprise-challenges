"""Figuras para o relatório (largura de página A4, sem título: a legenda vai no documento).

Reaproveita os cálculos do analise_resultados.ipynb (executa as células de código até a decomposição das
colunas, sem regravar as figuras do notebook) e grava graficos/relatorio_*.png e .pdf.

Dados: descompactar antes, na raiz, datasets/replicacao-cta-respostas.zip (cria data/column_type_annotation/...).

Uso, na raiz do repositório:  .venv/bin/python graficos_relatorio.py
"""
import contextlib, io, itertools, pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import numpy as np
from matplotlib.figure import Figure

ROOT = pathlib.Path(__file__).resolve().parent

# --- cálculos: os mesmos do notebook -------------------------------------------------------------------------------
nb = nbformat.read(ROOT / "analise_resultados.ipynb", 4)
ns = {"display": lambda *a, **k: None}
_savefig, _show = Figure.savefig, plt.show
Figure.savefig, plt.show = (lambda *a, **k: None), (lambda *a, **k: None)
with contextlib.redirect_stdout(io.StringIO()):
    for cell in nb.cells:
        if cell.cell_type == "code":
            exec(cell.source, ns)
            plt.close("all")
            if "decomp" in ns:
                break
Figure.savefig, plt.show = _savefig, _show

VERS, HDRS, REPL, MODELS = ns["VERS"], ns["HDRS"], ns["REPL"], ns["MODELS"]
BOOT, OBS, PAPER, ci, real, FULL = ns["BOOT"], ns["OBS"], ns["PAPER"], ns["ci"], ns["real"], ns["FULL"]

ALL5 = ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06", "gpt-6.1-terra", "claude-sonnet-5-5", "claude-haiku-5-5"]
NOME = {"gpt-4o-mini-2024-07-18": "GPT-4o-Mini", "gpt-4o-2024-08-06": "GPT-4o", "gpt-6.1-terra": "GPT-6.1 Terra",
        "claude-sonnet-5-5": "Claude Sonnet 5.5", "claude-haiku-5-5": "Claude Haiku 5.5"}
COR = ns["MODEL_COLOR"]
VER = dict(zip(VERS, ["Tabelas largas", "Alta esparsidade", "Nomes pouco\ndescritivos", "Tipos de dados\ncomplexos", "Todos os\ndesafios"]))
VER1 = {v: s.replace("\n", " ") for v, s in VER.items()}
COND = {"with-headers": "com nomes de coluna", "without-headers": "sem nomes de coluna"}

plt.rcParams.update({"font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                     "legend.fontsize": 8.5, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
num = lambda x, n=2: f"{x:.{n}f}".replace(".", ",")
TICKS = [0, 0.2, 0.4, 0.6, 0.8, 1.0]


def salvar(fig, nome):
    for ext in ("png", "pdf"):
        fig.savefig(ROOT / f"graficos/{nome}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


# --- Figura 1: valores do artigo e valores obtidos (GPT-4o-Mini e GPT-4o) -------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(6.7, 3.9), sharey=True)
for ax, m in zip(axes, REPL[::-1]):
    for i, v in enumerate(VERS):
        for h, dy, face in [("with-headers", 0.17, COR[m]), ("without-headers", -0.17, "white")]:
            y = len(VERS) - 1 - i + dy
            lo, hi = ci(BOOT[m, v, h]); p = PAPER[m][v][0 if h == "without-headers" else 1]
            ax.plot([lo, hi], [y, y], color=COR[m], lw=2, solid_capstyle="round", zorder=2)
            ax.plot(OBS[m, v, h], y, "o", ms=6.5, mfc=face, mec=COR[m], mew=1.7, zorder=3)
            ax.plot(p, y, marker="|", ms=12, mew=1.6, color="black", zorder=4)
            ax.text(1.06, y, f"{num(p)} → {num(OBS[m, v, h])}", va="center", ha="left", fontsize=7.5, color="#333333")
        if i:
            ax.axhline(len(VERS) - i - 0.5, color="#eeeeee", lw=0.8, zorder=0)
    ax.text(1.06, len(VERS) - 0.42, "artigo → obtido", va="bottom", ha="left", fontsize=7.5, color="#666666")
    ax.set_title(NOME[m], color=COR[m], fontweight="bold")
    ax.set_xlim(-0.03, 1.42); ax.set_ylim(-0.5, len(VERS) - 0.5); ax.set_xticks(TICKS); ax.set_xticklabels([num(t, 1) for t in TICKS])
    ax.spines["bottom"].set_bounds(0, 1); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#e3e3e3", lw=0.6); ax.set_axisbelow(True); ax.set_xlabel("F1 ponderado", x=0.35)
axes[0].set_yticks(range(len(VERS))); axes[0].set_yticklabels([VER[v] for v in reversed(VERS)])
hs = [plt.Line2D([], [], marker="o", ls="none", ms=6.5, mfc="#555555", mec="#555555", mew=1.7, label="obtido, com nomes de coluna"),
      plt.Line2D([], [], marker="o", ls="none", ms=6.5, mfc="white", mec="#555555", mew=1.7, label="obtido, sem nomes de coluna"),
      plt.Line2D([], [], color="#555555", lw=2, label="IC 95%"),
      plt.Line2D([], [], marker="|", ls="none", ms=12, mew=1.6, color="black", label="valor do artigo")]
fig.legend(handles=hs, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.06), columnspacing=1.2, handletextpad=0.4)
fig.tight_layout()
salvar(fig, "relatorio_replicacao")

# --- Figura 2: os cinco modelos em cada versão do conjunto ---------------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(6.7, 6.0), sharex=True)
w = 0.16
for ax, h in zip(axes, HDRS):
    for j, m in enumerate(ALL5):
        x = np.arange(len(VERS)) + (j - 2) * w
        val = np.array([OBS[m, v, h] for v in VERS]); lim = np.array([ci(BOOT[m, v, h]) for v in VERS])
        ax.bar(x, val, width=w - 0.02, color=COR[m], label=NOME[m], zorder=2)
        ax.errorbar(x, val, yerr=[val - lim[:, 0], lim[:, 1] - val], fmt="none", ecolor="#333333", elinewidth=0.8, zorder=3)
        for xi, vi, hi in zip(x, val, lim[:, 1]):
            ax.text(xi, hi + 0.02, num(vi), ha="center", va="bottom", rotation=90, fontsize=6.8, color="#333333")
    ax.set_title(COND[h].capitalize(), loc="left", fontweight="bold")
    ax.set_ylim(0, 1.22); ax.set_yticks(TICKS); ax.set_yticklabels([num(t, 1) for t in TICKS]); ax.spines["left"].set_bounds(0, 1)
    ax.set_ylabel("F1 ponderado", y=0.41); ax.grid(axis="y", color="#e3e3e3", lw=0.6); ax.set_axisbelow(True)
    ax.set_xticks(range(len(VERS))); ax.set_xticklabels([VER[v] for v in VERS]); ax.tick_params(axis="x", length=0)
axes[0].tick_params(labelbottom=False)
hd, lb = axes[0].get_legend_handles_labels()
fig.legend(hd, lb, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.035), columnspacing=1.2, handlelength=1.2)
fig.tight_layout()
salvar(fig, "relatorio_cinco_modelos")

# --- Figura 3: o que acontece com cada coluna avaliada -------------------------------------------------------------
r = real[real.fase == FULL].copy()
r["cat"] = np.select([r.ok, r.pred == "unspecified", (r.pred == "MISSING") | ~r.pred_valida], ["correta", "abstencao", "invalida"], default="errada")
CATS = [("correta", "tipo correto", "#009E73"), ("errada", "tipo errado", "#D55E00"),
        ("abstencao", 'resposta "unspecified" (abstenção)', "#8C8C8C"), ("invalida", "sem resposta ou rótulo fora da lista", "#F0E442")]
dec = r.groupby(["model", "ver", "hdr"]).cat.value_counts(normalize=True).unstack(fill_value=0)
fig, axes = plt.subplots(len(VERS), 2, figsize=(6.7, 7.2), sharex=True, sharey=True)
for i, v in enumerate(VERS):
    for k, h in enumerate(HDRS):
        ax = axes[i, k]; left = np.zeros(len(ALL5))
        for c, lab, cor in CATS:
            val = np.array([dec.loc[(m, v, h), c] for m in ALL5])
            ax.barh(range(len(ALL5)), val, left=left, color=cor, edgecolor="white", linewidth=0.8, height=0.72, label=lab)
            if c == "abstencao":
                for yy, (a, b) in enumerate(zip(left, val)):
                    if b >= 0.08:
                        ax.text(a + b / 2, yy, f"{round(b * 100)}%", ha="center", va="center", fontsize=6.8, color="white")
            left += val
        ax.set_xlim(0, 1); ax.invert_yaxis() if not ax.yaxis_inverted() else None
        ax.set_title(f"{VER1[v]} · {COND[h].replace(' de coluna', '')}", loc="left", fontsize=8.5)
        ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
axes[0, 0].set_yticks(range(len(ALL5))); axes[0, 0].set_yticklabels([NOME[m] for m in ALL5])
for ax in axes[-1]:
    ax.set_xlabel("proporção das colunas avaliadas")
hd, lb = axes[0, 0].get_legend_handles_labels()
fig.legend(hd, lb, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.055), columnspacing=1.5, handlelength=1.2)
fig.tight_layout(h_pad=0.9)
salvar(fig, "relatorio_tipos_de_resposta")

# --- Figura 1b: artigo e replicação em barras lado a lado (versão mais simples da Figura 1) ------------------------
VERC = dict(zip(VERS, ["Tabelas\nlargas", "Alta\nesparsidade", "Nomes pouco\ndescritivos", "Tipos\ncomplexos", "Todos os\ndesafios"]))
fig, axes = plt.subplots(2, 2, figsize=(6.7, 5.4), sharex=True, sharey=True)
w = 0.38
for i, h in enumerate(HDRS):
    for k, m in enumerate(REPL[::-1]):
        ax = axes[i, k]; x = np.arange(len(VERS))
        art = np.array([PAPER[m][v][0 if h == "without-headers" else 1] for v in VERS]); obt = np.array([OBS[m, v, h] for v in VERS])
        ax.bar(x - w / 2, art, width=w - 0.03, color="#B8B8B8", label="artigo", zorder=2)
        ax.bar(x + w / 2, obt, width=w - 0.03, color=COR[m], label="replicação", zorder=2)
        for xs, vals in [(x - w / 2, art), (x + w / 2, obt)]:
            for xi, vi in zip(xs, vals):
                ax.text(xi, vi + 0.015, num(vi), ha="center", va="bottom", fontsize=6.1, color="#333333")
        ax.set_title(f"{NOME[m]} · {COND[h]}", loc="left", fontsize=9, fontweight="bold")
        ax.set_ylim(0, 1.05); ax.set_yticks(TICKS); ax.set_yticklabels([num(t, 1) for t in TICKS])
        ax.grid(axis="y", color="#e3e3e3", lw=0.6); ax.set_axisbelow(True)
        ax.set_xticks(x); ax.set_xticklabels([VERC[v] for v in VERS], fontsize=6.5); ax.tick_params(axis="x", length=0)
    axes[i, 0].set_ylabel("F1 ponderado")
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color="#B8B8B8", label="valor publicado no artigo")] + [Patch(color=COR[m], label=f"replicação ({NOME[m]})") for m in REPL[::-1]],
           loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.045), handlelength=1.2)
fig.tight_layout()
salvar(fig, "relatorio_replicacao_barras")

# --- Figura 3b: tipos de resposta só na versão com todos os desafios -----------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(6.7, 2.5), sharey=True)
v = "all-challenges"
for ax, h in zip(axes, HDRS):
    left = np.zeros(len(ALL5))
    for c, lab, cor in CATS:
        val = np.array([dec.loc[(m, v, h), c] for m in ALL5])
        ax.barh(range(len(ALL5)), val, left=left, color=cor, edgecolor="white", linewidth=0.8, height=0.72, label=lab)
        for yy, (a, b) in enumerate(zip(left, val)):
            if b >= 0.07:
                ax.text(a + b / 2, yy, f"{round(b * 100)}%", ha="center", va="center", fontsize=7, color="black" if c == "invalida" else "white")
        left += val
    ax.set_xlim(0, 1); ax.set_title(COND[h].capitalize(), loc="left", fontsize=9, fontweight="bold")
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"]); ax.set_xlabel("proporção das colunas avaliadas")
axes[0].invert_yaxis(); axes[0].set_yticks(range(len(ALL5))); axes[0].set_yticklabels([NOME[m] for m in ALL5])
hd, lb = axes[0].get_legend_handles_labels()
fig.legend(hd, lb, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.2), columnspacing=1.5, handlelength=1.2)
fig.tight_layout()
salvar(fig, "relatorio_tipos_de_resposta_todos_desafios")

print("gravadas em graficos/: relatorio_replicacao, relatorio_replicacao_barras, relatorio_cinco_modelos, "
      "relatorio_tipos_de_resposta, relatorio_tipos_de_resposta_todos_desafios (.png e .pdf)")
