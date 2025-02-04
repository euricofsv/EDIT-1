
################################################
- A API está integrada numa pagina html e serve para fazer o upload de ficheiros parquet, oferecendo funcionalidades de pré-visualização no browser das primeiras linhas (isto pode ser usado com qualquer ficheiro parquet. Contudo a opção de geração de KPIs em formato Excel só será criado se o ficheiro parquet tiver a estrutura do ficheiro disponibilizado nas aulas da EDIT no curso DATA OPS)

############ Funcionalidades ###############
- Pré-visualização de ficheiros Parquet: Exibe as primeiras 5 linhas do ficheiro Parquet selecionado.
- Geração de KPIs: Processa o ficheiro Parquet e gera um ficheiro Excel com alguns KPIs.

############## Como Usar ################
###### Pré-requisitos

- Chrome, Firefox, Edge
- Ficheiro "dados_sensores_5000.parquet" ou um outro com a mesma estrutura

Como usar ###### 

1. **Selecionar o ficheiro Parquet**:
   - Clique no botão "Clique para selecionar o ficheiro Parquet" para escolher o ficheiro desejado.

2. **Pré-visualizar o ficheiro**:
   - Após selecionar o ficheiro, clique no botão "Pré-visualizar" para ver as primeiras 5 linhas do ficheiro Parquet.

3. **Gerar KPIs**:
   - Clique no botão "GERAR KPIs" para processar o ficheiro e gerar um ficheiro Excel com os KPIs calculados. O ficheiro será baixado automaticamente.

### Endpoints da API
/preview_parquet: Recebe o ficheiro Parquet e retorna as primeiras 5 linhas para pré-visualização em html.
/processar_parquet: Recebe o ficheiro Parquet, processa os dados e retorna um ficheiro Excel com alguns KPIs.
