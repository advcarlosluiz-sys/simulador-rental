import zipfile
import os

# Pega a pasta atual onde o script está
source_dir = os.path.dirname(os.path.abspath(__file__))
# O arquivo será criado na mesma pasta
output_file = "rental_smart_deploy.zip"

ignore_list = ['.env', 'instance', '__pycache__', 'leads_diagnosticos.db', 'leads_diagnosticos_v2.db', 'tmp_cleanup.py', 'zip_maker.py', '.venv', '.git']

def create_zip():
    try:
        count = 0
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                dirs[:] = [d for d in dirs if d not in ignore_list]
                for file in files:
                    if file not in ignore_list:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
                        count += 1
                        
        print(f"Sucesso! Arquivo '{output_file}' criado com {count} arquivos.")
        print(f"Localização: {os.path.abspath(output_file)}")
    except Exception as e:
        print(f"Erro ao criar ZIP: {e}")

if __name__ == "__main__":
    create_zip()
