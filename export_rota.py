#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KML – Gerar a ROTA a partir de um Excel (aba EXPORT_KML), em árvore:
  pasta por HORA > pasta a cada 10 MINUTOS > linha (LineString) por MINUTO
Com caminho fixo para entrada e saída
"""

import pandas as pd
import numpy as np
import simplekml
from pathlib import Path

# ===== CONFIGURAÇÕES FIXAS =====
CAMINHO_EXCEL = Path("files_in/in.xlsx")
CAMINHO_KML = Path("files_out/rota.kml")

# Pausa máxima entre dois minutos para ainda ligar a linha de um ao outro
INTERVALO_MAX_LIGACAO = pd.Timedelta(minutes=2)


def gerar_rota_kml(caminho_excel: Path, caminho_saida: Path):
    # Lê Excel
    # df = pd.read_excel(caminho_excel)
    df = pd.read_excel(caminho_excel, sheet_name="EXPORT_KML")
    

    # Normaliza colunas
    df.columns = [c.strip().upper().replace(":", "") for c in df.columns]
   

    # Seleciona colunas relevantes
    # df = df[["EVENT_TS", "LAT_FILE", "LON_FILE"]]
    df = df[["EVENT_TS", "LAT_FILE", "LON_FILE"]]

    # Converte tipos
    df["EVENT_TS"] = pd.to_datetime(df["EVENT_TS"], errors="coerce", utc=False)
    df["LAT_FILE"] = pd.to_numeric(df["LAT_FILE"], errors="coerce")
    df["LON_FILE"] = pd.to_numeric(df["LON_FILE"], errors="coerce")

    # Remove linhas inválidas
    df = df.dropna(subset=["EVENT_TS", "LAT_FILE", "LON_FILE"])
    df = df[(np.isfinite(df["LAT_FILE"])) & (np.isfinite(df["LON_FILE"]))]

    if df.empty:
        raise ValueError("Nenhum ponto válido após limpeza.")

    # Ordena por data/hora
    df = df.sort_values("EVENT_TS").reset_index(drop=True)

    if len(df) < 2:
        raise ValueError("É necessário pelo menos 2 pontos para a rota.")

    # Chaves de agrupamento: hora / 10 minutos / minuto
    df["HORA"] = df["EVENT_TS"].dt.floor("h")
    df["BLOCO_10MIN"] = df["EVENT_TS"].dt.floor("10min")
    df["MINUTO"] = df["EVENT_TS"].dt.floor("min")

    # Cria KML com um estilo compartilhado por todas as linhas
    kml = simplekml.Kml()
    estilo = simplekml.Style()
    estilo.linestyle.width = 3
    estilo.linestyle.color = simplekml.Color.blue

    # Último ponto do minuto anterior, para ligar um minuto ao seguinte
    ultimo_ponto = None
    ultimo_ts = None

    for hora, df_hora in df.groupby("HORA", sort=True):
        pasta_hora = kml.newfolder(name=hora.strftime("%Y-%m-%d %H:00"))

        for bloco, df_bloco in df_hora.groupby("BLOCO_10MIN", sort=True):
            fim_bloco = bloco + pd.Timedelta(minutes=9)
            pasta_bloco = pasta_hora.newfolder(
                name=f"{bloco.strftime('%H:%M')} – {fim_bloco.strftime('%H:%M')}"
            )

            for minuto, df_min in df_bloco.groupby("MINUTO", sort=True):
                coords = list(zip(df_min["LON_FILE"].tolist(), df_min["LAT_FILE"].tolist()))

                # Liga ao minuto anterior, exceto se houve uma pausa longa nos dados
                primeiro_ts = df_min["EVENT_TS"].iloc[0]
                if ultimo_ponto is not None and primeiro_ts - ultimo_ts <= INTERVALO_MAX_LIGACAO:
                    coords.insert(0, ultimo_ponto)

                ultimo_ponto = coords[-1]
                ultimo_ts = df_min["EVENT_TS"].iloc[-1]

                if len(coords) < 2:
                    continue

                linha = pasta_bloco.newlinestring(name=f"Rota {minuto.strftime('%H:%M')}")
                linha.coords = coords
                linha.style = estilo
                linha.altitudemode = simplekml.AltitudeMode.clamptoground

    # Salva arquivo
    kml.save(str(caminho_saida))
    print(f"KML is done: {caminho_saida}")


if __name__ == "__main__":
    gerar_rota_kml(CAMINHO_EXCEL, CAMINHO_KML)
