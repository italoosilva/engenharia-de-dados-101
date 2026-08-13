"""
ingestao.py - Camada BRONZE
============================

OBJETIVO DESTA CAMADA
----------------------
A camada bronze é a porta de entrada dos dados no seu pipeline. A regra de
ouro aqui é: **não limpe, não corrija, não descarte nada**. Você só precisa:

  1. Ler cada arquivo da pasta `lakehouse/landing/` (um .csv, um .json e um .txt),
     cada um com seu próprio formato e suas próprias "sujeiras".
  2. Transformar cada um em uma lista de dicionários (uma linha = um registro).
  3. Acrescentar DUAS colunas de metadados de ingestão em cada registro:
       - "arquivo_origem": o nome do arquivo de onde o registro veio
       - "dt_ingestao": data/hora (ISO 8601) em que a ingestão foi executada
  4. Salvar o resultado em `lakehouse/bronze/saida/`, um CSV por origem:
       - lakehouse/bronze/saida/vendas_bronze.csv
       - lakehouse/bronze/saida/clientes_bronze.csv
       - lakehouse/bronze/saida/produtos_bronze.csv

Ou seja: a bronze é uma cópia FIEL do que está na landing, só que já
estruturada (todo mundo virou uma tabela) e com rastreabilidade (você sabe
de onde e quando cada linha veio). Linhas duplicadas, valores vazios,
datas em formatos diferentes, tudo isso continua exatamente como está.
Isso é problema da camada silver, não da bronze!

Depois de rodar este script, use `python lakehouse/bronze/verificar_bronze.py` para
conferir se sua ingestão está correta.

Dica sobre as bibliotecas padrão que você vai precisar:
  - csv        -> para ler vendas.csv e escrever os arquivos de saída
  - json       -> para ler clientes.json
  - datetime   -> para gerar o timestamp de ingestão
  - pathlib    -> para lidar com caminhos de arquivo
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

LAKEHOUSE = Path(__file__).parent.parent
LANDING = LAKEHOUSE / "landing"
SAIDA = Path(__file__).parent / "saida"

# Use o mesmo timestamp para todos os registros de uma mesma execução.
DT_INGESTAO = datetime.now(timezone.utc).isoformat()


def ler_vendas_csv() -> list[dict]:
    caminho_vendas = LANDING / "vendas.csv"
    with open(caminho_vendas, "r", encoding="utf-8") as arquivo:
        vendas = list(csv.DictReader(arquivo))
    return vendas


def ler_clientes_json() -> list[dict]:
    caminho_clientes = LANDING / "clientes.json"
    with open(caminho_clientes, "r", encoding="utf-8") as arquivo:
        clientes = json.load(arquivo)
    return clientes


def ler_produtos_txt() -> list[dict]:

    caminho_produtos = LANDING / "produtos.txt"
    with open(caminho_produtos, "r", encoding="utf-8") as arquivo:
        linhas = arquivo.readlines()
        colunas = None
        produtos = []
        for linha in linhas:
            produto = {}
            linha_limpa = linha.strip()

            if not linha_limpa or linha_limpa.startswith("#"):
                continue 

            if not colunas:
                colunas = list(linha_limpa.split("|"))
                continue

            dados = linha_limpa.split("|")
            for i in range(len(dados)):
                produto[colunas[i]] =  dados[i]
            produtos.append(produto)

    return produtos


def adicionar_metadados(registros: list[dict], nome_arquivo: str) -> list[dict]:
    """Acrescenta as colunas arquivo_origem e dt_ingestao a cada registro."""
    for registro in registros:
        registro["arquivo_origem"] = nome_arquivo
        registro["dt_ingestao"] = DT_INGESTAO
    return registros


def salvar_csv(registros: list[dict], caminho_saida: Path, colunas: list[str]) -> None:
    """Escreve uma lista de dicionários em um arquivo CSV, na ordem de `colunas`."""
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_saida, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for registro in registros:
            escritor.writerow({coluna: registro.get(coluna, "") for coluna in colunas})


def main() -> None:
    vendas = adicionar_metadados(ler_vendas_csv(), "vendas.csv")
    clientes = adicionar_metadados(ler_clientes_json(), "clientes.json")
    produtos = adicionar_metadados(ler_produtos_txt(), "produtos.txt")

    salvar_csv(
        vendas,
        SAIDA / "vendas_bronze.csv",
        ["id_venda", "id_cliente", "id_produto", "quantidade", "data_venda", "valor_total", "arquivo_origem", "dt_ingestao"],
    )
    salvar_csv(
        clientes,
        SAIDA / "clientes_bronze.csv",
        ["id_cliente", "nome", "email", "cidade", "estado", "data_cadastro", "telefone", "arquivo_origem", "dt_ingestao"],
    )
    salvar_csv(
        produtos,
        SAIDA / "produtos_bronze.csv",
        ["id_produto", "nome", "categoria", "preco", "ativo", "arquivo_origem", "dt_ingestao"],
    )

    print(f"vendas_bronze.csv:   {len(vendas)} linhas")
    print(f"clientes_bronze.csv: {len(clientes)} linhas")
    print(f"produtos_bronze.csv: {len(produtos)} linhas")
    print("\nAgora rode: python lakehouse/bronze/verificar_bronze.py")


if __name__ == "__main__":
    main()
