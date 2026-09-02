#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KML 3.0 – Pastas por HORA, rotas (LineString) por MINUTO
Gera um único KML contendo:
  - Uma pasta para cada HORA (YYYY-MM-DD HH:00)
  - Dentro de cada pasta, uma rota (LineString) para cada MINUTO (HH:MM) conectando os pontos daquele minuto

Requisitos:
  pip install pandas simplekml openpyxl

Ajuste os caminhos em CONFIGURAÇÕES FIXAS antes de executar.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import simplekml


# ===== CONFIGURAÇÕES FIXAS =====
CAMINHO_EXCEL = Path("files_in/in.xlsx")
CAMINHO_SAIDA_KML = Path("files_out/rota.kml")

# Estilo da linha
LARGURA_LINHA = 3
#COR_LINHA = simplekml.Color.green
COR_LINHA = simplekml.Color.red


def normalizar_colunas(cols):
    """
    Remove espaços extras, dois-pontos finais e deixa MAIÚSCULO para mapear colunas.
    """
    norm = []
    for c in cols:
        c2 = str(c).strip().replace("\n", " ")
        if c2.endswith(":"):
            c2 = c2[:-1]
        norm.append(c2.upper())
    return norm


def mapear_colunas(df):
    """
    Tenta mapear colunas mesmo com variações de nome.
    Retorna os nomes originais das colunas de data, lat e lon.
    """
    cols_norm = normalizar_colunas(df.columns)
    mapa = {n: o for n, o in zip(cols_norm, df.columns)}

    def achar(*possiveis):
        for p in possiveis:
            if p in mapa:
                return mapa[p]
        return None

    col_data = achar("DATA_CREATE_ELEMENT", "DATA_CREATE", "DATA", "TIMESTAMP", "DATE", "DATETIME")
    col_lat = achar("LATITUDE", "LAT", "Y")
    col_lon = achar("LONGITUDE", "LON", "LONG", "X")

    faltando = [n for n, c in [("DATA_CREATE_ELEMENT", col_data), ("LATITUDE", col_lat), ("LONGITUDE", col_lon)] if c is None]
    if faltando:
        raise ValueError(f"Não encontrei as colunas necessárias no Excel: {', '.join(faltando)}")

    return col_data, col_lat, col_lon


def resumir_posicoes_duplicadas_por_minuto(df):
    """
    Para cada minuto, mostra exatamente:
      - quantos pares GPS distintos existem (LAT, LON únicos)
      - quantas ocorrências repetidas existem no total (posicoes iguais)

    Exemplo:
      par A aparece 4 vezes, par B aparece 2 vezes
      -> pares GPS distintos = 2
      -> posicoes iguais = 6
    """
    df = df.copy()
    df["MINUTO"] = df["DATA"].dt.floor("min")

    resumo = (
        df.groupby(["MINUTO", "LAT", "LON"], dropna=False)
        .size()
        .reset_index(name="qtde")
    )

    pares_por_minuto = resumo.groupby("MINUTO").size().rename("pares_gps_distintos")
    ocorrencias_repetidas = resumo[resumo["qtde"] > 1].groupby("MINUTO")["qtde"].sum().rename("posicoes_iguais")

    agrupado = pares_por_minuto.to_frame().join(ocorrencias_repetidas, how="left")
    agrupado["pares_gps_distintos"] = agrupado["pares_gps_distintos"].fillna(0).astype(int)
    agrupado["posicoes_iguais"] = agrupado["posicoes_iguais"].fillna(0).astype(int)
    agrupado = agrupado.reset_index().sort_values("MINUTO")

    print("\nResumo por minuto: pares GPS distintos vs. ocorrências repetidas")
    print(f"{'MINUTO':<20} {'PARES GPS':>12} {'POSICOES IGUAIS':>18}")
    for _, r in agrupado.iterrows():
        minuto = r["MINUTO"].strftime("%Y-%m-%d %H:%M")
        print(
            f"{minuto:<20} "
            f"{int(r['pares_gps_distintos']):>12} "
            f"{int(r['posicoes_iguais']):>18}"
        )

    total_pares = int(agrupado["pares_gps_distintos"].sum())
    total_iguais = int(agrupado["posicoes_iguais"].sum())
    print(f"\nTOTAL: {total_pares} pares GPS distintos | {total_iguais} posições iguais em todos os minutos.")
    print("Obs.: 'pares GPS distintos' = número de combinações únicas de LAT+LON; 'posicoes iguais' = total de ocorrências repetidas dessas combinações.")


def gerar_kml_pasta_hora_rotas_minuto(caminho_excel: Path, caminho_kml: Path):
    # Leitura
    df = pd.read_excel(caminho_excel)
    col_data, col_lat, col_lon = mapear_colunas(df)

    df = df[[col_data, col_lat, col_lon]].rename(
        columns={col_data: "DATA", col_lat: "LAT", col_lon: "LON"}
    )

    # Tipos
    df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", utc=False)
    df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
    df["LON"] = pd.to_numeric(df["LON"], errors="coerce")

    # Limpeza
    df = df.dropna(subset=["DATA", "LAT", "LON"])
    df = df[(np.isfinite(df["LAT"])) & (np.isfinite(df["LON"]))]
    if df.empty:
        raise ValueError("Nenhum ponto válido após limpeza.")

    # Ordena por tempo
    df = df.sort_values("DATA").reset_index(drop=True)

    # Chaves de agrupamento
    df["HORA"] = df["DATA"].dt.floor("h")    # ex.: 2025-08-18 10:00:00
    df["MINUTO"] = df["DATA"].dt.floor("min")  # ex.: 2025-08-18 10:23:00

    # Resumo de coordenadas duplicadas por minuto
    resumir_posicoes_duplicadas_por_minuto(df)

    # Cria KML
    kml = simplekml.Kml()

    # Grupo por HORA
    for hora, df_hora in df.groupby("HORA", sort=True):
        pasta_hora = kml.newfolder(name=hora.strftime("%Y-%m-%d %H:00"))

        # Para cada MINUTO dentro da HORA, cria a rota
        for minuto, df_min in df_hora.groupby("MINUTO", sort=True):
            # Ordena os pontos daquele minuto
            df_min = df_min.sort_values("DATA")

            # Monta coordenadas (lon, lat)
            coords = list(zip(df_min["LON"].tolist(), df_min["LAT"].tolist()))
            if len(coords) < 2:
                # Com 1 ponto, não faz line. Se quiser, pode criar um ponto isolado.
                # Aqui ignoramos para manter apenas rotas.
                continue

            nome = f"Rota {minuto.strftime('%H:%M')}"
            ls = pasta_hora.newlinestring(name=nome)
            ls.coords = coords
            ls.style.linestyle.width = LARGURA_LINHA
            ls.style.linestyle.color = COR_LINHA
            ls.altitudemode = simplekml.AltitudeMode.clamptoground

    # Salva
    kml.save(str(caminho_kml))
    print(f"KML gerado: {caminho_kml}")
    

if __name__ == "__main__":
    gerar_kml_pasta_hora_rotas_minuto(CAMINHO_EXCEL, CAMINHO_SAIDA_KML)
