import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

mapa_classi = {
    1: "Confirmado (laboratorialmente)",
    2: "Descartado",
    3: "Provável",
    4: "Suspeito",
    5: "Perda de seguimento",
    6: "Exclusão",
    8: "Não indicado"
}

# Carregar os arquivos
df25 = pd.read_csv("MPX_2025_OPENDATASUS.csv", sep=";")
df26 = pd.read_csv("MPX_2026_OPENDATASUS.csv", sep=";")


def analisar_tempos(df):
    df = df.copy()

    # Garantir que as datas estejam no formato correto
    datas = [
        "data_inicio_sintomas",
        "data_notificacao",
        "data_concluida"
    ]

    for col in datas:
        df[col] = pd.to_datetime(
            df[col], errors="coerce", dayfirst=True
        )

    # Calcular intervalos
    df["tempo_notificacao"] = (
        df["data_notificacao"] -
        df["data_inicio_sintomas"]
    ).dt.days

    df["tempo_conclusao"] = (
        df["data_concluida"] -
        df["data_notificacao"]
    ).dt.days

    for col in ["tempo_notificacao", "tempo_conclusao"]:
        print(f"\n--- {col.upper()} ---")

        valores = df[col]
        negativos = (valores < 0).sum()

        # Excluir intervalos negativos das estatísticas
        validos = valores[valores >= 0].dropna()

        print(f"Registros válidos: {len(validos)}")
        print(f"Dados ausentes: {valores.isna().sum()}")
        print(f"Intervalos negativos: {negativos}")

        if validos.empty:
            continue

        print(validos.describe(
            percentiles=[.25, .50, .75, .90, .95]
        ).round(2))

        print(
            df.loc[
                df["tempo_notificacao"].idxmax()
            ]
        )

        for dias in [7, 14, 30]:
            percentual = (validos > dias).mean() * 100
            print(f"Acima de {dias} dias: {percentual:.2f}%")

    resumo = (
    df.groupby("classificacao_final")
    [["tempo_notificacao", "tempo_conclusao"]]
    .agg(["count", "mean", "median", "std"])
    .round(2)
    )

    print(resumo)

def create_notification_frame(df):
    new_df = pd.DataFrame({
        "classificacao_final": df["classi_fin"],
        "data_inicio_sintomas": df["dt_sin_pri"],
        "data_notificacao": df["dt_notific"],
        "data_concluida": df["dt_conclusao"],
        "evolucao": df["evolucao"],
    })

    # Substituir códigos por descrições
    new_df["classificacao_final"] = (
        pd.to_numeric(new_df["classificacao_final"], errors="coerce")
        .map(mapa_classi)
    )

    # Converter datas
    cols_datas = [
        "data_inicio_sintomas",
        "data_notificacao",
        "data_concluida"
    ]

    for col in cols_datas:
        new_df[col] = pd.to_datetime(
            new_df[col],
            dayfirst=True,
            errors="coerce"
        )

    # Intervalo entre sintomas e notificação
    new_df["tempo_notificacao_dias"] = (
        new_df["data_notificacao"]
        - new_df["data_inicio_sintomas"]
    ).dt.days

    return new_df


    
# Juntar os dados
df = pd.concat([df25, df26], ignore_index=True)

print(df["classi_fin"]);
print(df.columns.tolist())

# Converter datas
df["data"] = pd.to_datetime(
    df["dt_notific"],
    format="%d/%m/%Y",
    errors="coerce"
)

# print(df);
df["ano"] = df["data"].dt.year
df["mes"] = df["data"].dt.month

# print(df);

notificacao_df = create_notification_frame(df)
# pd.set_option("display.max_rows", 10)
# pd.set_option("display.max_columns", None)
# pd.set_option("display.width", 20)
# pd.set_option("display.max_colwidth", None)
print(notificacao_df)

contagem = notificacao_df["classificacao_final"].value_counts()
percentual = notificacao_df["classificacao_final"].value_counts(normalize=True) * 100

for nome, qtd in contagem.items():
    print(f"{nome}: {qtd} ({percentual[nome]:.2f}%)")

analisar_tempos(notificacao_df)



notificacao_df.to_csv(
    "notificacoes.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig",
    na_rep="Não indicado"
)
exit()
confirmados = df[df["classi_fin"].astype("string") == "1"].copy()

# Contar notificações por mês e ano
mensal = (
    confirmados.groupby(["mes", "ano"])
    .size()
    .unstack(fill_value=0)
    .reindex(index=range(1, 13), columns=[2025, 2026], fill_value=0)
)

print("Mensal: ")
print(mensal)
print(mensal.index)    # Meses
print(mensal.columns)  # Anos
print(mensal.shape)    # (12, 2)

print(f'2025: {mensal[2025].sum()} (expected: 1119)')
print(f'2026: {mensal[2026].sum()} (expected: 665)')
exit()

meses = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]

x = np.arange(12)
largura = 0.35

fig, ax = plt.subplots(figsize=(12, 5))

ax.bar(x - largura/2, mensal[2025],
       largura, label="2025", color="#A855F7")

ax.bar(x + largura/2, mensal[2026],
       largura, label="2026", color="#22D33E")

ax.set_xticks(x)
ax.set_xticklabels(meses)
ax.set_ylabel("Número de notificações")
ax.set_title("Notificações de mpox por mês — 2025 e 2026")

ax.grid(axis="y", linestyle=":", color="#3478D5", alpha=0.6)
ax.set_axisbelow(True)
ax.legend()

plt.tight_layout()
plt.savefig("comparativo_mpox.png", dpi=300)
plt.show()