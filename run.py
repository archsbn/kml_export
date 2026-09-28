import sys
from pathlib import Path

import export_rota

PASTA_BASE = Path(sys.argv[0]).resolve().parent

CAMINHO_EXCEL = PASTA_BASE / "files_in" / "in.xlsm"
CAMINHO_KML = PASTA_BASE / "files_out" / "rota.kml"


def main():
    CAMINHO_KML.parent.mkdir(parents=True, exist_ok=True)

    if not CAMINHO_EXCEL.exists():
        print(f"File not found: {CAMINHO_EXCEL}")
        return

    # export_rota.export_detail()
    export_rota.gerar_rota_kml(CAMINHO_EXCEL, CAMINHO_KML)
    print(f"Rota exported in: {CAMINHO_KML}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}")
    input("ENTER TO EXIT.")