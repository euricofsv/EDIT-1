from flask import Flask, request, send_file, render_template, jsonify
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl import load_workbook
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import io

app = Flask(__name__)

#pagina inicial
@app.route("/")
def home():
    return render_template("Index.html")

#endpoint para criar o ficheiro dos kpis a partir do ficheiro da aula/exercicio
@app.route("/processar_parquet", methods=["POST"])
def processar_parquet():
    #verifica se o arquivo foi enviado
    if "file" not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files["file"]

    #read
    try:
        df = pd.read_parquet(file)
    except Exception as e:
        return f"Erro ao ler o arquivo Parquet: {str(e)}", 400

    #verificar se as colunas necessárias existem
    required_columns = ["empresa", "energia_kwh", "agua_m3", "co2_emissoes", "setor"]
    for col in required_columns:
        if col not in df.columns:
            return f"Coluna '{col}' não encontrada no arquivo Parquet", 400

    #corrigir erro do datetime(nao faz nada com o ficheiro de exemplo)
    #df["PurchaseDate"] = pd.to_datetime(df["PurchaseDate"], errors="coerce")

    #crrigir nulos e números
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("N/A")  # Corrigir com "N/A" se a coluna for string
        else:
            df[col] = df[col].fillna(0)  # Corrigir com 0 se a coluna for numérica

    #alterar os brancos para "Not Applicable"(nao faz nada com o ficheiro de exemplo)
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: "N/A" if isinstance(x, str) and x.strip() == "" else x)

    #remover duplicados(nao faz nada com o ficheiro de exemplo)
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        df = df.drop_duplicates()


    #arrendondar números float para 2 casas decimais
    #df["TotalPrice"] = df["TotalPrice"].round(2)
    #df["PricePerUnit"] = df["PricePerUnit"].round(2)

     # KPIs
     # Verificar se as colunas necessárias existem
    required_columns = ["empresa", "energia_kwh", "agua_m3", "co2_emissoes", "setor"]
    for col in required_columns:
        if col not in df.columns:
            return f"Coluna '{col}' não encontrada no arquivo Parquet", 400

    # Corrigir nulos e números
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("N/A")  # Corrigir com "N/A" se a coluna for string
        else:
            df[col] = df[col].fillna(0)  # Corrigir com 0 se a coluna for numérica

    # Alterar os brancos para "Not Applicable"
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: "N/A" if isinstance(x, str) and x.strip() == "" else x)

    # Remover duplicados
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        df = df.drop_duplicates()

    # Normalizar os dados para garantir que energia, água e CO2 tenham o mesmo peso
    scaler = MinMaxScaler()
    df[["energia_kwh_norm", "agua_m3_norm", "co2_emissoes_norm"]] = scaler.fit_transform(
        df[["energia_kwh", "agua_m3", "co2_emissoes"]]
    )

    ###KPIS
      # Calcular uma pontuação combinada (soma dos valores normalizados)
    df["pontuacao_combinada"] = df["energia_kwh_norm"] + df["agua_m3_norm"] + df["co2_emissoes_norm"]

    # Top 10 empresas que mais gastam (energia, água e CO2 combinados)
    top10_mais_gastam = df.nlargest(10, "pontuacao_combinada")[
        ["empresa", "energia_kwh", "agua_m3", "co2_emissoes", "pontuacao_combinada"]
    ]

    # Top 10 empresas que menos gastam (energia, água e CO2 combinados)
    top10_menos_gastam = df.nsmallest(10, "pontuacao_combinada")[
        ["empresa", "energia_kwh", "agua_m3", "co2_emissoes", "pontuacao_combinada"]
    ]

    # 1. Comparação entre setores
    consumo_por_setor = df.groupby("setor").agg({
        "energia_kwh": ["sum", "mean"],
        "agua_m3": ["sum", "mean"],
        "co2_emissoes": ["sum", "mean"]
    }).reset_index()

    # Renomear colunas para facilitar a leitura
    consumo_por_setor.columns = [
        "Setor",
        "Energia Total (kWh)",
        "Energia Média (kWh)",
        "Água Total (m³)",
        "Água Média (m³)",
        "CO₂ Total",
        "CO₂ Médio"
    ]

    # 2. Identificar tendências ou padrões
    # Exemplo: Setores com alta emissão de CO₂ em relação ao consumo de energia
    df["co2_por_energia"] = df["co2_emissoes"] / df["energia_kwh"]
    tendencia_co2_energia = df.groupby("setor")["co2_por_energia"].mean().reset_index()
    tendencia_co2_energia.columns = ["Setor", "CO₂ por Energia (kg/kWh)"]

    # Exemplo: Setores que consomem muita água em relação à energia
    df["agua_por_energia"] = df["agua_m3"] / df["energia_kwh"]
    tendencia_agua_energia = df.groupby("setor")["agua_por_energia"].mean().reset_index()

    # Criar um arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Top 10 empresas que mais gastam
        top10_mais_gastam.to_excel(writer, sheet_name="Top 10 mais consumo", index=False)

        # Top 10 empresas que menos gastam
        top10_menos_gastam.to_excel(writer, sheet_name="Top 10 menos consumo", index=False)

        # Comparação entre setores
        consumo_por_setor.to_excel(writer, sheet_name="Setores", index=False)

        # Tendências e padrões
        tendencia_co2_energia.to_excel(writer, sheet_name="Tendência de CO₂ por Energia", index=False)

    # Retorna o ficheiro KPIs como resposta
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"KPIs_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )

#endpoint para pré-visualização do arquivo Parquet
@app.route('/preview_parquet', methods=['POST'])
def preview_parquet():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum ficheiro enviado'}), 400 

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum ficheiro selecionado'}), 400

    try:
        #read
        df = pd.read_parquet(file)

        #converte as primeiras 5 linhas para HTML
        preview_html = df.head().to_html(index=False, classes="table table-striped")

        #html da tabela
        return preview_html
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Executar a aplicação
if __name__ == "__main__":
    app.run(debug=True)

# Para implantação no Render:
#import os
#if __name__ == "__main__":
    # port = int(os.environ.get("PORT", 5000))  # Usa a porta definida pelo Render ou 5000 como fallback
    # app.run(host="0.0.0.0", port=port, debug=False)  