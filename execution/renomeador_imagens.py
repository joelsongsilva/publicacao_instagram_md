import os
import re
import argparse
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description="Renomeia imagens exportadas do Canva para o formato YYYY-MM-DD_1.png e YYYY-MM-DD_2.png")
    parser.add_argument("--dir", type=str, required=True, help="Diretório onde estão as imagens (ex: 1.png, 2.png, 3.png...)")
    parser.add_argument("--start_date", type=str, required=True, help="Data do primeiro dia do mês no formato YYYY-MM-DD")
    
    args = parser.parse_args()
    directory = args.dir
    start_date_str = args.start_date
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        print("Erro: A data deve estar no formato YYYY-MM-DD")
        return

    if not os.path.isdir(directory):
        print(f"Erro: O diretório '{directory}' não existe.")
        return

    # Pega todos os arquivos e filtra apenas os PNGs
    arquivos = [f for f in os.listdir(directory) if f.lower().endswith('.png')]
    
    # Extrai o numero do nome do arquivo (ex: "1.png" -> 1) para ordernar corretamente
    def extract_number(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else 0
        
    arquivos.sort(key=extract_number)
    
    if len(arquivos) % 2 != 0:
        print(f"Aviso: O número de imagens ({len(arquivos)}) é ímpar! Deveriam ser 2 por dia.")

    print(f"Iniciando renomeação em: {directory}")
    print(f"Total de arquivos encontrados: {len(arquivos)}")
    
    renomeados = 0
    # Agrupa de 2 em 2 (Card 1 e Card 2)
    for i in range(0, len(arquivos), 2):
        current_date_obj = start_date + timedelta(days=i//2)
        current_date = current_date_obj.strftime("%Y-%m-%d")
        
        # O arquivo ímpar (1, 3, 5...) é o card da Mensagem
        old1 = os.path.join(directory, arquivos[i])
        new1 = os.path.join(directory, f"{current_date}_1.png")
        os.rename(old1, new1)
        renomeados += 1
        print(f"{arquivos[i]} -> {current_date}_1.png")
        
        # O arquivo par (2, 4, 6...) é o card do Link
        if i + 1 < len(arquivos):
            old2 = os.path.join(directory, arquivos[i+1])
            new2 = os.path.join(directory, f"{current_date}_2.png")
            os.rename(old2, new2)
            renomeados += 1
            print(f"{arquivos[i+1]} -> {current_date}_2.png")

    print(f"Sucesso! {renomeados} arquivos renomeados com formato YYYY-MM-DD_x.png.")
    print("Pronto para fazer o upload no Google Drive.")

if __name__ == "__main__":
    main()
