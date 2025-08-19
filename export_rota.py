#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KML 2.0 – Gerar apenas a ROTA (LineString) a partir de um Excel
Com caminho fixo para entrada e saída
"""

import pandas as pd
import numpy as np
import simplekml
from pathlib import Path

# ===== CONFIGURAÇÕES FIXAS =====
CAMINHO_EXCEL = Path("files_in/in.xlsx")
CAMINHO_KML = Path("files_out/rota.kml")


def gerar_rota_kml(caminho_excel: Path, caminho_saida: Path):
    # Lê Excel
    df = pd.read_excel(caminho_excel)

    # Normaliza colunas
    df.columns = [c.strip().upper().replace(":", "") for c in df.columns]

    # Seleciona colunas relevantes
    df = df[["DATA_CREATE_ELEMENT", "LATITUDE", "LONGITUDE"]]

    # Converte tipos
    df["DATA_CREATE_ELEMENT"] = pd.to_datetime(df["DATA_CREATE_ELEMENT"], errors="coerce", utc=False)
    df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")

    # Remove linhas inválidas
    df = df.dropna(subset=["DATA_CREATE_ELEMENT", "LATITUDE", "LONGITUDE"])
    df = df[(np.isfinite(df["LATITUDE"])) & (np.isfinite(df["LONGITUDE"]))]

    if df.empty:
        raise ValueError("Nenhum ponto válido após limpeza.")

    # Ordena por data/hora
    df = df.sort_values("DATA_CREATE_ELEMENT").reset_index(drop=True)

    # Prepara coordenadas (lon, lat)
    coords = list(zip(df["LONGITUDE"].tolist(), df["LATITUDE"].tolist()))

    if len(coords) < 2:
        raise ValueError("É necessário pelo menos 2 pontos para a rota.")

    # Cria KML
    kml = simplekml.Kml()
    t0 = df["DATA_CREATE_ELEMENT"].iloc[0]
    t1 = df["DATA_CREATE_ELEMENT"].iloc[-1]
    nome_rota = f"Rota {t0.strftime('%Y-%m-%d %H:%M:%S')} → {t1.strftime('%Y-%m-%d %H:%M:%S')}"

    linha = kml.newlinestring(name=nome_rota)
    linha.coords = coords
    linha.style.linestyle.width = 3
    linha.style.linestyle.color = simplekml.Color.blue
    linha.altitudemode = simplekml.AltitudeMode.clamptoground

    # Salva arquivo
    kml.save(str(caminho_saida))
    print(f"KML gerado com sucesso: {caminho_saida}")


if __name__ == "__main__":
    gerar_rota_kml(CAMINHO_EXCEL, CAMINHO_KML)
