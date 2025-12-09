import ckanapi
import random
from datetime import datetime
import os

# Configuração para rodar dentro do container
CKAN_URL = "http://localhost:5000"
API_KEY = os.environ.get('CKAN_API_KEY')

if not API_KEY:
    print("Erro: CKAN_API_KEY não definida.")
    exit(1)

def seed_data():
    ckan = ckanapi.RemoteCKAN(CKAN_URL, apikey=API_KEY)

    print(f"Conectando ao CKAN em {CKAN_URL}...")

    # 1. Criar Organizações
    orgs = ['org-a', 'org-b']
    for org_name in orgs:
        try:
            print(f"Criando organização: {org_name}")
            ckan.action.organization_create(name=org_name, title=f"Organização {org_name.upper()}")
        except Exception as e:
            print(f"  > Organização {org_name} (provavelmente já existe)")

    # 2. Criar Grupos
    groups = ['grupo-1', 'grupo-2']
    for group_name in groups:
        try:
            print(f"Criando grupo: {group_name}")
            ckan.action.group_create(name=group_name, title=f"Grupo {group_name.upper()}")
        except Exception as e:
            print(f"  > Grupo {group_name} (provavelmente já existe)")

    # 3. Criar Datasets e Recursos
    dataset_prefixes = ['dados-financeiros', 'relatorio-anual', 'indicadores-saude', 'transporte-publico', 'obras-viarias']
    
    resource_terms = [
        "Disponibilidade", "Faturamento", "Cronograma", "Anexo", "Planilha", 
        "Relatório", "Dados Brutos", "Metadados", "Log", "Resumo"
    ]
    formats = ['CSV', 'PDF', 'XLSX', 'JSON', 'XML']

    print("Criando datasets e recursos...")
    for i in range(10):
        org = random.choice(orgs)
        group = random.choice(groups)
        prefix = random.choice(dataset_prefixes)
        name = f"{prefix}-{i:03d}-{random.randint(1000,9999)}"
        title = f"{prefix.replace('-', ' ').title()} {i:03d}"

        try:
            pkg = ckan.action.package_create(
                name=name,
                title=title,
                owner_org=org,
                groups=[{'name': group}],
                notes=f"Dataset de teste gerado automaticamente. Contém dados sobre {prefix}.",
                private=False
            )
            print(f"  + Dataset criado: {name}")
            
            # Criar 5 recursos para este dataset
            for j in range(5):
                term = random.choice(resource_terms)
                fmt = random.choice(formats)
                res_name = f"{term} - {fmt} - {i}-{j}"
                
                ckan.action.resource_create(
                    package_id=pkg['id'],
                    name=res_name,
                    description=f"Arquivo de {term} referente ao dataset {title}.",
                    format=fmt,
                    url="http://example.com/demo_resource.csv" 
                )
                print(f"    - Recurso adicionado: {res_name}")

        except Exception as e:
            print(f"  ! Erro ao criar dataset {name}: {e}")

    print("\nCarga de dados concluída!")

if __name__ == '__main__':
    seed_data()