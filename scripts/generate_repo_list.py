import os
import requests
import json
import subprocess
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Configuración
ORG_NAME = "fastlane"
TOKEN = os.getenv("GITHUB_TOKEN")


def get_active_repos(org):
    url = f"https://api.github.com/orgs/{org}/repos"
    params = {"per_page": 100, "sort": "pushed"}

    # Se añade el token a los headers para evitar límites de la API de GitHub
    headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return []

    repos = response.json()

    # Calcular la fecha de hace un mes
    one_month_ago = datetime.now() - timedelta(days=30)
    repo_list = []

    for r in repos:
        # Filtrar por fecha de último push (commit)
        pushed_at = datetime.strptime(r['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")

        if pushed_at > one_month_ago:
            repo_list.append({
                # Usamos clone_url (termina en .git) que es ideal para clonar
                "url": r['clone_url'],
                "path": f"data/repos/{r['name']}",
                "ref": r['default_branch']
            })

    return repo_list


# 1. Asegurar que los directorios existan
os.makedirs("./data/repos", exist_ok=True)

# 2. Generar la estructura final y buscar los repositorios
active_repos = get_active_repos(ORG_NAME)
output = {"repositories": active_repos}

# 3. Guardar en archivo JSON en la nueva ruta
json_path = "./data/repos.json"
with open(json_path, 'w') as f:
    json.dump(output, f, indent=4)

print(f"Se han encontrado {len(active_repos)} repositorios activos.")
print(f"Lista guardada exitosamente en: {json_path}")

# 4. Clonar los repositorios hacia data/repos
print("\n--- Iniciando clonación de repositorios ---")
for repo in active_repos:
    repo_url = repo["url"]
    repo_path = repo["path"]

    # Comprobar si la carpeta ya existe para no intentar clonarlo dos veces
    if not os.path.exists(repo_path):
        print(f"Clonando {repo_url} en {repo_path}...")
        # Ejecuta el comando git clone en la terminal de forma invisible
        subprocess.run(["git", "clone", repo_url, repo_path])
    else:
        print(f"El repositorio ya existe en {repo_path}. Omitiendo...")

print("\n¡Proceso finalizado! Ya tienes tus repositorios listos para generar el SBOM.")
