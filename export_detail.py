import pandas as pd
import simplekml
import os
from datetime import timedelta

# ===== CONFIGURAÇÕES =====
arquivo_excel = "in.xlsx"       # caminho do seu Excel
saida_base = "kml_saida"        # pasta onde tudo será salvo
intervalo_arquivos_min = 1      # cada arquivo cobre 30 minutos

# Criar pasta base de saída
os.makedirs(saida_base, exist_ok=True)

# Ler dados
df = pd.read_excel(arquivo_excel)
df.columns = [c.strip() for c in df.columns]  # remover espaços
df = df[['DATA_CREATE_ELEMENT', 'LATITUDE', 'LONGITUDE']]

# Converter data
df['DATA_CREATE_ELEMENT'] = pd.to_datetime(df['DATA_CREATE_ELEMENT'])
df = df.sort_values(by='DATA_CREATE_ELEMENT')

# Determinar o intervalo total
inicio_total = df['DATA_CREATE_ELEMENT'].min()
fim_total = df['DATA_CREATE_ELEMENT'].max()

# Loop para criar arquivos de 1 hora
atual_inicio = inicio_total
while atual_inicio < fim_total:
    atual_fim = atual_inicio + timedelta(hours=intervalo_arquivos_min)
    
    # Filtrar dados do intervalo
    df_intervalo = df[(df['DATA_CREATE_ELEMENT'] >= atual_inicio) &
                      (df['DATA_CREATE_ELEMENT'] < atual_fim)]
    
    if not df_intervalo.empty:
        # Criar KML para este intervalo
        kml = simplekml.Kml()
        
        for minuto, df_min in df_intervalo.groupby(df_intervalo['DATA_CREATE_ELEMENT'].dt.floor('min')):
            pasta_minuto = kml.newfolder(name=minuto.strftime('%Y-%m-%d %H:%M'))
            
            # Criar pontos por segundo
            for _, row in df_min.iterrows():
                pasta_minuto.newpoint(
                    name=row['DATA_CREATE_ELEMENT'].strftime('%H:%M:%S'),
                    coords=[(row['LONGITUDE'], row['LATITUDE'])]
                    
                )
            
            # Criar rota (LineString)
            coords = list(zip(df_min['LONGITUDE'], df_min['LATITUDE']))
            if len(coords) > 1:
                linha = pasta_minuto.newlinestring(name=f"Rota {minuto.strftime('%H:%M')}")
                linha.coords = coords
                linha.style.linestyle.width = 2
                linha.style.linestyle.color = simplekml.Color.blue
        
        # Nome do arquivo
        nome_arquivo = f"rota_{atual_inicio.strftime('%Y-%m-%d_%Hh%M')}-{atual_fim.strftime('%Hh%M')}.kml"
        caminho_arquivo = os.path.join(saida_base, nome_arquivo)
        kml.save(caminho_arquivo)
        print(f"Arquivo gerado: {caminho_arquivo}")
    
    atual_inicio = atual_fim

print("Processo concluído!")
