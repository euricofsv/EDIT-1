from flask import Flask, request, send_file, render_template
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl import load_workbook
from datetime import datetime
import io

app = Flask(__name__)

#Rota para a página inicial com o formulário de upload
@app.route("/")
def home():
    return render_template("Index.html")

#Rota para processar o arquivo Parquet
@app.route("/processar_parquet", methods=["POST"])
def processar_parquet():
    #Verifica se o arquivo foi enviado
    if "file" not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files["file"]

    #Ler o arquivo Parquet
    try:
        df = pd.read_parquet(file)
    except Exception as e:
        return f"Erro ao ler o arquivo Parquet: {str(e)}", 400

    #Corrigir erro do datetime
    df["PurchaseDate"] = pd.to_datetime(df["PurchaseDate"], errors="coerce")

    #corrigir nulos e numeros
    for col in df.columns:
        if df[col].dtype == "object": 
            df[col] = df[col].fillna("N/A")  # #corrigir com na se a coluna for string
        else:
           df[col] = df[col].fillna(0) #corrigir com 0 se a colunar for numerica

    #alterar os brancos para not applicable
    for col in df.columns:
        if df[col].dtype == "object":  
            df[col] = df[col].apply(lambda x: "N/A" if isinstance(x, str) and x.strip() == "" else x)

    #remover duplciados
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        #print(f"foram encontradas {duplicates} linhas duplicadas")
        df = df.drop_duplicates()


    #valores numéricos como string
    colunas_num = ["TotalPrice", "PricePerUnit", "Quantity", "CustomerID"]
    for col in colunas_num:
        if df[col].apply(lambda x: isinstance(x, str)).any():
            #print(f"A coluna '{col}' tem valores não numéricos")
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col].fillna(0, inplace=True)
            #print(f"Valores não numéricos na coluna '{col}' foram alterados")

    #arredondar números float para 2 casas decimais
    df["TotalPrice"] = df["TotalPrice"].round(2)
    df["PricePerUnit"] = df["PricePerUnit"].round(2)

    #KPIs
    receita_total = df["TotalPrice"].sum()
    media_vendas = df["TotalPrice"].mean()
    total_transacoes = df["TransactionID"].nunique()
    total_itens_vendidos = df["Quantity"].sum()
    vendas_por_categoria = df.groupby("Category")["TotalPrice"].sum()

    top_produtos = df.groupby(["Region", "ProductName"])["Quantity"].sum().reset_index()
    top_produtos = top_produtos.sort_values(by=["Region", "Quantity"], ascending=[True, False])
    top_produtos = top_produtos.groupby("Region").head(5).reset_index(drop=True)

    vendas_por_regiao = df.groupby("Region")["TotalPrice"].sum()
    media_quantidade_vendida = df["Quantity"].mean()
    vendas_por_metodo_pagamento = df.groupby("PaymentMethod")["TotalPrice"].sum()
    invoice_medio_por_cliente = df.groupby("CustomerID")["TotalPrice"].sum().mean()
    vendas_acima_5000 = df[df["TotalPrice"] > 5000].shape[0]
    vendas_por_categoria_regiao = df.groupby(["Category", "Region"])["TotalPrice"].sum()
    transacoes_por_periodo = df.groupby(df["PurchaseDate"].dt.to_period("D")).size()
    vendas_diarias = df.groupby(df["PurchaseDate"].dt.date)["TotalPrice"].sum()
    clientes_unicos = df["CustomerID"].nunique()

    #Dicionário de KPIs
    resultados = {
        "KPI": [
            "Receita Total",
            "Média de Vendas por Transação",
            "Total de Transações",
            "Quantidade Total de Produtos Vendidos",
            "Invoice Médio por Cliente",
            "Transações Acima de 5000€",
            "Total de Clientes Únicos"
        ],
        "Valor": [
            receita_total,
            media_vendas,
            total_transacoes,
            total_itens_vendidos,
            invoice_medio_por_cliente,
            vendas_acima_5000,
            clientes_unicos
        ]
    }

    #KPIs para DataFrame
    df_resultados = pd.DataFrame(resultados)

    #Vendas por categoria
    vendas_por_categoria_df = vendas_por_categoria.reset_index()
    vendas_por_categoria_df.columns = ['Categoria', 'Vendas']

    #Vendas por categoria e região
    vendas_por_categoria_regiao_df = vendas_por_categoria_regiao.reset_index()
    vendas_por_categoria_regiao_df.columns = ['Categoria', 'Região', 'Vendas']

    #Top 5 produtos
    top_produtos_df = top_produtos.reset_index()
    top_produtos_df.columns = ['ID', 'Regiao', 'Produto', 'Quantidade Vendida (TOP 5)']

    #Vendas por método de pagamento
    vendas_por_metodo_pagamento_df = vendas_por_metodo_pagamento.reset_index()
    vendas_por_metodo_pagamento_df.columns = ['Método de Pagamento', 'Vendas']

    #Vendas diárias
    vendas_diarias_df = vendas_diarias.reset_index()
    vendas_diarias_df.columns = ['Data', 'Vendas Diárias']

    #Criar um arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_resultados.to_excel(writer, sheet_name="KPIS", index=False)
        vendas_diarias_df.to_excel(writer, sheet_name="Vendas Diárias", index=False)
        vendas_por_categoria_df.to_excel(writer, sheet_name="Vendas por Categoria", index=False)
        vendas_por_categoria_regiao_df.to_excel(writer, sheet_name="Vendas por Categoria e Região", index=False)
        top_produtos_df.to_excel(writer, sheet_name="Top Produtos", index=False)
        vendas_por_metodo_pagamento_df.to_excel(writer, sheet_name="Vendas por Método de Pagamento", index=False)

    #Retornar o arquivo Excel como resposta
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"KPIs_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )

#Executar a aplicação
#if __name__ == "__main__":
#    app.run(debug=True)

#colocar este pedaço de codigo para funcionar no render
#import os

if __name__ == "__main__":
   import os
   port = int(os.environ.get("PORT", 5000))  # Usa a porta definida pelo Render ou 5000 como fallback
   app.run(host="0.0.0.0", port=port, debug=False)  # Desative o debug em produção
