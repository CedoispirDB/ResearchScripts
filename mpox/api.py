import json
import time
from pathlib import Path

import pandas as pd
import requests

URL = "https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/mpox"

LIMIT = 1000
PASTA = Path("paginas_mpox")
PASTA.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({"Accept": "application/json"})


def buscar_pagina(offset):
    arquivo = PASTA / f"pagina_{offset:05d}.json"

    # Se já foi baixada, reutilizar
    if arquivo.exists():
        print(f"Página {offset}: recuperada do disco")
        return json.loads(arquivo.read_text(encoding="utf-8"))

    # Tentar novamente em caso de erro
    for tentativa in range(1, 6):
        try:
            resposta = session.get(
                URL,
                params={"limit": LIMIT, "offset": offset},
                timeout=(15, 120)
            )

            resposta.raise_for_status()
            registros = resposta.json()["mpox"]

            # Salvar primeiro em arquivo temporário
            temporario = arquivo.with_suffix(".tmp")
            temporario.write_text(
                json.dumps(registros, ensure_ascii=False),
                encoding="utf-8"
            )
            temporario.replace(arquivo)

            return registros

        except (requests.RequestException, ValueError, KeyError) as erro:
            print(f"Tentativa {tentativa}/5 falhou: {erro}")

            if tentativa == 5:
                raise

            time.sleep(2 ** tentativa)


# Baixar todas as páginas
offset = 0

while True:
    print(f"Consultando página {offset}...")

    registros = buscar_pagina(offset)

    if not registros:
        break

    if len(registros) < LIMIT:
        break

    offset += 1
    time.sleep(0.2)


# Reunir apenas registros de 2025 e 2026
frames = []

for i in range(offset + 1):
    arquivo = PASTA / f"pagina_{i:05d}.json"
    registros = json.loads(arquivo.read_text(encoding="utf-8"))

    if not registros:
        continue

    pagina = pd.DataFrame(registros)

    datas = pd.to_datetime(
        pagina["dt_notific"],
        format="mixed",
        dayfirst=True,
        errors="coerce"
    )

    pagina = pagina[datas.dt.year.isin([2025, 2026])]

    if not pagina.empty:
        frames.append(pagina)

if not frames:
    raise ValueError("Nenhum registro de 2025 ou 2026 encontrado.")

df = pd.concat(frames, ignore_index=True)

datas = pd.to_datetime(
    df["dt_notific"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

df25 = df[datas.dt.year == 2025]
df26 = df[datas.dt.year == 2026]

df25.to_csv("mpox_2025.csv", sep=";", index=False)
df26.to_csv("mpox_2026.csv", sep=";", index=False)
df.to_csv("mpox_2025_2026.csv", sep=";", index=False)

print("Download concluído!")
print("2025:", len(df25))
print("2026:", len(df26))