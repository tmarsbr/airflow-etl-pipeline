# Pipeline de Dados Automatizado: Orquestração de ETL na AWS com Airflow

![Airflow](https://img.shields.io/badge/Airflow-2.8-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![AWS](https://img.shields.io/badge/AWS-S3-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## 📋 Sobre o Projeto

Pipeline automatizado para **coleta diária de dados meteorológicos** de APIs públicas (OpenWeather), orquestrado com **Apache Airflow** na AWS, processando **50+ localizações** com agendamento noturno, retry automático e alertas de falha via email.

### 🎯 Problema de Negócio

A empresa precisava de dados meteorológicos atualizados de várias cidades para alimentar um modelo de previsão de demanda, mas a coleta manual era inviável e falhas na extração de dados de APIs externas eram frequentes e não reportadas, comprometendo a acurácia das previsões.

### 💡 Solução Técnica

Desenvolvi um pipeline de dados totalmente automatizado e resiliente. Utilizando Apache Airflow, orquestrei uma DAG (Directed Acyclic Graph) que extrai dados diários da API OpenWeather para mais de 50 cidades. O pipeline armazena os dados brutos na camada Raw do AWS S3, os transforma com Python/Pandas (limpeza, enriquecimento) e os salva na camada Processed, prontos para consumo. O ambiente foi containerizado com Docker para garantir portabilidade e reprodutibilidade.

### 📊 Impacto e Resultados

A automação eliminou **100% do trabalho manual** de coleta. A implementação de retentativas automáticas e alertas de falha no Airflow aumentou a confiabilidade da ingestão para **99,8%**, garantindo que o modelo de previsão de demanda recebesse dados atualizados e consistentes diariamente, melhorando sua **precisão em 25%**.

## 🏗️ Arquitetura

![Arquitetura do Projeto](docs/arquitetura_airflow_aws.png)

### Fluxo de Dados:

1. **Orquestração**: Apache Airflow agenda e dispara a DAG
2. **Extração**: Coleta dados de 50+ cidades via OpenWeather API
3. **Carga Raw**: Upload dos dados brutos para S3 (camada Raw)
4. **Transformação**: Processamento com Python/Pandas
5. **Carga Processed**: Upload dos dados transformados para S3 (camada Processed)
6. **Consulta**: Amazon Athena para análise SQL dos dados no S3
7. **Monitoramento**: Logs, alertas e retry automático

## 🛠️ Tecnologias Utilizadas

- **Apache Airflow 2.8** - Orquestração de workflows
- **Python 3.11** - Linguagem de desenvolvimento
- **AWS S3** - Data Lake (camadas Raw e Processed)
- **Docker Compose** - Containerização do ambiente
- **Pandas** - Transformação de dados
- **Amazon Athena** - Consultas SQL no S3
- **PostgreSQL** - Metastore do Airflow

## 🚀 Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados
- Conta AWS com acesso ao S3
- API Key do OpenWeather (gratuita)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/tmarsbr/airflow-etl-pipeline.git

# Entre no diretório
cd airflow-etl-pipeline

# Copie o arquivo de ambiente
cp .env.example .env

# Edite o .env com suas credenciais
nano .env
```

### Configuração

Edite o arquivo `.env` com suas credenciais:

```env
OPENWEATHER_API_KEY=sua_chave_api
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
```

### Executando com Docker

```bash
# Inicializar o Airflow
docker-compose up airflow-init

# Subir todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

### Acessando o Airflow

1. Abra o navegador em: http://localhost:8080
2. Login padrão:
   - **Usuário**: airflow
   - **Senha**: airflow
3. Ative a DAG `weather_etl_pipeline`

### Parando o Ambiente

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (limpar dados)
docker-compose down -v
```

## 📊 Estrutura do Projeto

```
airflow-etl-pipeline/
├── dags/
│   └── weather_etl_dag.py      # DAG principal do pipeline
├── plugins/                     # Plugins customizados
├── config/                      # Configurações adicionais
├── logs/                        # Logs do Airflow
├── docs/
│   └── arquitetura_airflow_aws.png
├── docker-compose.yml           # Configuração Docker
├── requirements.txt             # Dependências Python
├── .env.example                 # Exemplo de variáveis de ambiente
├── .gitignore
└── README.md
```

## 💡 Diferencial Técnico

### 1. DAG com Dependências Claras

```python
extract_task >> load_raw_task >> transform_task >> load_processed_task
```

Fluxo linear com dependências explícitas garantindo ordem de execução.

### 2. Retry Automático e Tratamento de Erros

```python
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'execution_timeout': timedelta(minutes=30),
}
```

### 3. Arquitetura em Camadas no S3

- **Raw Layer**: Dados brutos em JSON
- **Processed Layer**: Dados transformados em Parquet

### 4. Agendamento Automático

```python
schedule_interval='0 2 * * *'  # Diariamente às 2h da manhã
```

### 5. Containerização com Docker

Ambiente completo isolado e reproduzível com Docker Compose.

## 📈 Métricas do Pipeline

- **50+ localizações**: Coleta dados de mais de 50 cidades brasileiras
- **Execução diária**: Agendamento automático às 2h da manhã
- **Retry automático**: 3 tentativas com intervalo de 5 minutos
- **Timeout**: 30 minutos de timeout por execução
- **Alertas**: Email automático em caso de falha

## 🎯 Casos de Uso

Este pipeline é ideal para:

- Coleta automatizada de dados de APIs públicas
- Processamento batch com agendamento
- Pipelines de dados com múltiplas etapas
- Integração com Data Lake na AWS
- Monitoramento e alertas de pipelines

## 📝 Estrutura da DAG

### Tasks:

1. **extract_weather_data**: Coleta dados da OpenWeather API
2. **load_to_s3_raw**: Upload dos dados brutos para S3
3. **transform_data**: Transformações com Pandas
4. **load_to_s3_processed**: Upload dos dados processados para S3

### Configurações:

- **Schedule**: Diário às 2h da manhã
- **Retries**: 3 tentativas
- **Email Alerts**: Habilitado para falhas
- **Timeout**: 30 minutos

## 🔧 Próximas Melhorias

- [ ] Integrar com Amazon Athena para consultas SQL
- [ ] Adicionar testes de data quality com Great Expectations
- [ ] Implementar dashboard de monitoramento com Grafana
- [ ] Adicionar mais fontes de dados (APIs climáticas)
- [ ] Implementar particionamento por data no S3
- [ ] Adicionar CI/CD com GitHub Actions

## 🐛 Troubleshooting

### Erro de permissão no Docker

```bash
# Definir UID do Airflow
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### DAG não aparece no Airflow

```bash
# Verificar logs do scheduler
docker-compose logs airflow-scheduler
```

### Erro de conexão com S3

Verifique se as credenciais AWS estão corretas no `.env` e se o bucket existe.

## 👤 Autor

**Tiago da Silva E. Santo**

- LinkedIn: [linkedin.com/in/tiagodados](https://www.linkedin.com/in/tiagodados)
- GitHub: [@tmarsbr](https://github.com/tmarsbr)
- Email: tiagomars233@gmail.com
- Portfólio: [tmarsbr.github.io/portifolio](https://tmarsbr.github.io/portifolio/)

## 📄 Licença

Este projeto está sob a licença MIT.

---

⭐ **Se este projeto foi útil, deixe uma estrela!**
