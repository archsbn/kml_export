import export_rota
from pathlib import Path

CAMINHO_EXCEL = Path("files_in/in.xlsx")
CAMINHO_KML = Path("files_out/rota.kml")



## Execute all date, 1h / 1m / 1 sec + route
# export_detail()


## Execute all date, 1h / 1m / 1 sec + route
export_rota.gerar_rota_kml(CAMINHO_EXCEL, CAMINHO_KML)
