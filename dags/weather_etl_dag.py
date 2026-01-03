"""
DAG para Pipeline ETL de Dados Meteorológicos
Coleta diária de dados de 50+ localizações via OpenWeather API
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import requests
import json
import pandas as pd
import os

# Configurações padrão da DAG
default_args = {
    'owner': 'tiago',
    'depends_on_past': False,
    'email': ['tiagomars233@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# Lista de cidades para coletar dados
CITIES = [
    'São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza',
    'Belo Horizonte', 'Manaus', 'Curitiba', 'Recife', 'Porto Alegre',
    'Belém', 'Goiânia', 'Guarulhos', 'Campinas', 'São Luís',
    'São Gonçalo', 'Maceió', 'Duque de Caxias', 'Natal', 'Teresina',
]


def extract_weather_data(**context):
    """
    Extrai dados meteorológicos da API OpenWeather
    """
    api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    weather_data = []
    
    for city in CITIES:
        try:
            params = {
                'q': city,
                'appid': api_key,
                'units': 'metric',
                'lang': 'pt_br'
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extrair informações relevantes
            weather_record = {
                'city': city,
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'weather': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            weather_data.append(weather_record)
            print(f"✓ Dados coletados: {city}")
            
        except Exception as e:
            print(f"✗ Erro ao coletar dados de {city}: {str(e)}")
            continue
    
    # Salvar dados brutos localmente
    output_path = f"/tmp/weather_raw_{context['ds']}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(weather_data, f, ensure_ascii=False, indent=2)
    
    print(f"Total de registros coletados: {len(weather_data)}")
    return output_path


def load_to_s3_raw(**context):
    """
    Carrega dados brutos na camada Raw do S3
    """
    ti = context['ti']
    file_path = ti.xcom_pull(task_ids='extract_weather_data')
    
    s3_hook = S3Hook(aws_conn_id='aws_default')
    bucket_name = 'weather-data-pipeline'
    
    # Upload para camada Raw
    s3_key = f"raw/weather/{context['ds']}/weather_data.json"
    s3_hook.load_file(
        filename=file_path,
        key=s3_key,
        bucket_name=bucket_name,
        replace=True
    )
    
    print(f"✓ Dados carregados no S3: s3://{bucket_name}/{s3_key}")
    return s3_key


def transform_data(**context):
    """
    Transforma dados brutos em formato analítico
    """
    ti = context['ti']
    file_path = ti.xcom_pull(task_ids='extract_weather_data')
    
    # Ler dados brutos
    with open(file_path, 'r', encoding='utf-8') as f:
        weather_data = json.load(f)
    
    # Converter para DataFrame
    df = pd.DataFrame(weather_data)
    
    # Aplicar transformações
    df['temperature_category'] = pd.cut(
        df['temperature'],
        bins=[-float('inf'), 15, 25, float('inf')],
        labels=['Frio', 'Agradável', 'Quente']
    )
    
    df['humidity_category'] = pd.cut(
        df['humidity'],
        bins=[-float('inf'), 30, 60, float('inf')],
        labels=['Baixa', 'Normal', 'Alta']
    )
    
    # Adicionar metadados
    df['processed_at'] = datetime.now().isoformat()
    df['pipeline_version'] = '1.0'
    
    # Salvar dados transformados
    output_path = f"/tmp/weather_processed_{context['ds']}.parquet"
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Dados transformados: {len(df)} registros")
    return output_path


def load_to_s3_processed(**context):
    """
    Carrega dados processados na camada Processed do S3
    """
    ti = context['ti']
    file_path = ti.xcom_pull(task_ids='transform_data')
    
    s3_hook = S3Hook(aws_conn_id='aws_default')
    bucket_name = 'weather-data-pipeline'
    
    # Upload para camada Processed
    s3_key = f"processed/weather/{context['ds']}/weather_data.parquet"
    s3_hook.load_file(
        filename=file_path,
        key=s3_key,
        bucket_name=bucket_name,
        replace=True
    )
    
    print(f"✓ Dados processados carregados no S3: s3://{bucket_name}/{s3_key}")
    return s3_key


# Definir a DAG
with DAG(
    'weather_etl_pipeline',
    default_args=default_args,
    description='Pipeline ETL para coleta de dados meteorológicos',
    schedule_interval='0 2 * * *',  # Executa diariamente às 2h da manhã
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl', 'weather', 'aws', 's3'],
) as dag:
    
    # Task 1: Extrair dados da API
    extract_task = PythonOperator(
        task_id='extract_weather_data',
        python_callable=extract_weather_data,
        provide_context=True,
    )
    
    # Task 2: Carregar dados brutos no S3
    load_raw_task = PythonOperator(
        task_id='load_to_s3_raw',
        python_callable=load_to_s3_raw,
        provide_context=True,
    )
    
    # Task 3: Transformar dados
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
        provide_context=True,
    )
    
    # Task 4: Carregar dados processados no S3
    load_processed_task = PythonOperator(
        task_id='load_to_s3_processed',
        python_callable=load_to_s3_processed,
        provide_context=True,
    )
    
    # Definir dependências
    extract_task >> load_raw_task >> transform_task >> load_processed_task
