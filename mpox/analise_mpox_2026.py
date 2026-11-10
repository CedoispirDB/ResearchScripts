"""Análise exploratória das notificações de mpox (OpenDataSUS, 2026).

Requisitos: pip install pandas matplotlib
Uso: python analise_mpox_2026.py [caminho/do/arquivo.csv]

Observações:
- As contagens são de NOTIFICAÇÕES, sem filtro automático de casos confirmados.
- A classificação final apresenta códigos que não estão definidos no dicionário
  oficial consultado (26/05/2026): esses códigos NÃO são interpretados aqui.
- O mesmo ocorre com o código '0' em algumas variáveis categóricas.
- As medidas de CD4 usam somente valores >0 para pessoas com HIV='1';
  zeros e ausências devem ser investigados antes da interpretação clínica.

Dicionário oficial:
https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/mpox/dicionario_de_dados_mpox.pdf
"""
from pathlib import Path
import sys
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as 

# Nomes amigáveis -> nomes REAIS no CSV
mapa_colunas = {
    "Forma provável de transmissão": "transm",
    "UF de residência": "sg_uf",
    "UF de notificação": "sg_uf_not",
    "Data da notificação": "dt_notific",
    "Idade": "nu_idade_n",
    "Sexo": "cs_sexo",
    "Comportamento sexual": "comp_sexual",
    "Identidade de gênero": "ident_genero",
    "IST ativa": "ist_ativa",
    "Imunodeprimido": "pac_imunossup",
    "HIV positivo": "hiv",
    "Contagem de CD4": "contag_cd4",
    "Clado": "clado",
    "Classificação final": "classi_fin",
}

# Apenas categorias explicitamente documentadas no dicionário oficial.
# Códigos ausentes nestes mapas continuam visíveis como 'Código X (sem legenda)'.
rotulos = {
    "Forma provável de transmissão": {
        "1": "Animal para pessoa",
        "2": "Drogas intravenosas / transfusão",
        "3": "Associada à assistência à saúde",
        "4": "Transmissão vertical",
        "5": "Exposição em laboratório",
        "6": "Transmissão sexual",
        "7": "Material contaminado",
        "8": "Desconhecida",
        "9": "Outra",
    },
    "Sexo": {"1": "Masculino", "2": "Feminino", "3": "Intersexo", "9": "Ignorado"},
    "Comportamento sexual": {
        "1": "Relações sexuais com homens",
        "2": "Relações sexuais com mulheres",
        "3": "Relações sexuais com homens e mulheres",
        "9": "Ignorado",
    },
    "Identidade de gênero": {
        "1": "Mulher cisgênero",
        "2": "Homem cisgênero",
        "3": "Mulher transgênero",
        "4": "Homem transgênero",
        "5": "Travesti",
        "6": "Não binário",
        "7": "Não se aplica",
        "9": "Ignorado",
    },
    "IST ativa": {"1": "Sim", "2": "Não", "9": "Ignorado"},
    "Imunodeprimido": {
        "1": "Sim: doença", "2": "Sim: medicamento",
        "3": "Sim: causa desconhecida", "4": "Não", "9": "Ignorado",
    },
    "HIV positivo": {"1": "Sim", "2": "Não", "9": "Ignorado"},
    "Clado": {"1": "WA (África Ocidental)", "2": "CB (Bacia do Congo)",
              "3": "Outro", "9": "Ignorado"},
    "Classificação final": {"1": "Confirmado (laboratorialmente)", "3": "Provável"},
}


def ler_dados(arquivo: Path) -> pd.DataFrame:
    dados = pd.read_csv(arquivo, sep=";", dtype="string", encoding="utf-8-sig")
    faltantes = [col for col in mapa_colunas.values() if col not in dados.columns]
    if faltantes:
        raise ValueError(f"Colunas não encontradas no CSV: {faltantes}")
    dados = dados.rename(columns={v: k for k, v in mapa_colunas.items()})
    dados = dados[list(mapa_colunas)].copy()
    dados["Data da notificação"] = pd.to_datetime(
        dados["Data da notificação"], format="%d/%m/%Y", errors="coerce"
    )
    for col in ["Idade", "Contagem de CD4"]:
        dados[col] = pd.to_numeric(dados[col], errors="coerce")
    return dados


def salvar(fig, destino: Path) -> None:
    fig.savefig(destino, dpi=160, bbox_inches="tight")
    plt.close(fig)


def barras_categoricas(df: pd.DataFrame, coluna: str, destino: Path) -> pd.DataFrame:
    contagens = df[coluna].fillna("Ausente").value_counts()
    categorias = rotulos[coluna]

    def rotulo(codigo: str) -> str:
        if codigo == "Ausente":
            return "Ausente"
        descricao = categorias.get(str(codigo))
        return f"{codigo} — {descricao}" if descricao else f"Código {codigo} (sem legenda oficial)"

    legenda = [textwrap.fill(rotulo(str(c)), width=44) for c in contagens.index]
    altura = max(4.0, len(contagens) * 0.6 + 1.2)
    fig, ax = plt.subplots(figsize=(11, altura))
    barras = ax.barh(legenda[::-1], contagens.values[::-1])
    ax.bar_label(barras, padding=3, fontsize=9)
    ax.set_xlim(0, max(contagens.values) * 1.13 if len(contagens) else 1)
    ax.set_xlabel("Número de notificações")
    ax.set_title(f"Mpox 2026 — {coluna}")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    salvar(fig, destino)
    return pd.DataFrame({"categoria": [rotulo(str(c)) for c in contagens.index],
                         "quantidade": contagens.values, "variavel": coluna})


def barras_uf(df: pd.DataFrame, coluna: str, destino: Path) -> pd.DataFrame:
    counts = df[coluna].fillna("Ausente").value_counts().head(15).sort_values()
    fig, ax = plt.subplots(figsize=(10, 7))
    barras = ax.barh(counts.index.astype(str), counts.values)
    ax.bar_label(barras, padding=3)
    ax.set_xlim(0, counts.max() * 1.13)
    ax.set_xlabel("Número de notificações")
    ax.set_title(f"Mpox 2026 — 15 UFs com mais registros: {coluna}")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    salvar(fig, destino)
    return pd.DataFrame({"categoria": counts.index.astype(str), "quantidade": counts.values,
                         "variavel": coluna})


def grafico_mes(df: pd.DataFrame, destino: Path) -> pd.DataFrame:
    mes = df["Data da notificação"].dropna().dt.to_period("M").value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(mes.index.astype(str), mes.values, marker="o")
    for i, quantidade in enumerate(mes.values):
        ax.annotate(str(quantidade), (i, quantidade), xytext=(0, 7),
                    textcoords="offset points", ha="center")
    ax.set_title("Mpox 2026 — Notificações por mês")
    ax.set_xlabel("Mês da notificação")
    ax.set_ylabel("Número de notificações")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    salvar(fig, destino)
    return pd.DataFrame({"categoria": mes.index.astype(str), "quantidade": mes.values,
                         "variavel": "Data da notificação"})


def grafico_idade(df: pd.DataFrame, destino: Path) -> None:
    idades = df["Idade"].dropna()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(idades, bins=range(0, 101, 5), edgecolor="white")
    ax.set_title("Mpox 2026 — Distribuição da idade")
    ax.set_xlabel("Idade (anos)")
    ax.set_ylabel("Número de notificações")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    salvar(fig, destino)


def grafico_cd4(df: pd.DataFrame, destino: Path) -> None:
    # Valores 0 e ausentes não são usados neste histograma; NÃO significa CD4 negativo.
    valores = df.loc[(df["HIV positivo"] == "1") &
                     (df["Contagem de CD4"] > 0), "Contagem de CD4"].dropna()
    if valores.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(valores, bins=25, edgecolor="white")
    ax.set_title(f"Mpox 2026 — CD4 entre HIV positivos (n={len(valores)}; CD4 > 0)")
    ax.set_xlabel("Contagem de CD4 informada")
    ax.set_ylabel("Número de notificações")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    salvar(fig, destino)


def main():
    entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("MPX_2026_OPENDATASUS.csv")
    saida = Path(__file__).parent / "graficos_mpox_2026"
    saida.mkdir(exist_ok=True)
    df = ler_dados(entrada)
    print(f"Registros: {len(df):,}. Período: {df['Data da notificação'].min().date()} a {df['Data da notificação'].max().date()}")
    df.to_csv(saida / "mpox_variaveis_selecionadas.csv", sep=";", index=False, encoding="utf-8-sig")
    resumo = []
    resumo.append(grafico_mes(df, saida / "01_notificacoes_por_mes.png"))
    resumo.append(barras_uf(df, "UF de residência", saida / "02_uf_residencia.png"))
    resumo.append(barras_uf(df, "UF de notificação", saida / "03_uf_notificacao.png"))
    grafico_idade(df, saida / "04_distribuicao_idade.png")
    campos = [
        ("Sexo", "05_sexo"),
        ("Comportamento sexual", "06_comportamento_sexual"),
        ("Identidade de gênero", "07_identidade_genero"),
        ("IST ativa", "08_ist_ativa"),
        ("Imunodeprimido", "09_imunodeprimido"),
        ("HIV positivo", "10_hiv_positivo"),
        ("Forma provável de transmissão", "11_forma_transmissao"),
        ("Clado", "12_clado"),
        ("Classificação final", "13_classificacao_final"),
    ]
    for coluna, nome in campos:
        resumo.append(barras_categoricas(df, coluna, saida / f"{nome}.png"))
    grafico_cd4(df, saida / "14_contagem_cd4_hiv_positivo.png")
    pd.concat(resumo, ignore_index=True).to_csv(saida / "resumo_contagens.csv", index=False, encoding="utf-8-sig")
    print(f"Gráficos, CSV e resumo gerados em: {saida.resolve()}")
    print("ATENÇÃO: classificação final tem códigos não documentados no dicionário oficial consultado.")

if __name__ == "__main__":
    main()
