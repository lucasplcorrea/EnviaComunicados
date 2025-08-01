import pandas as pd
import os
import logging
import requests
import time
import random
import base64
from datetime import datetime
import mimetypes
from dotenv import load_dotenv
from status_manager import StatusManager
import sys
import shutil
import json

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f'envio_comunicados_evolution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ComunicadosSenderEvolution:
    def __init__(self, server_url, api_key, instance_name):
        """
        Inicializa o cliente Evolution API para envio de comunicados
        
        Args:
            server_url: URL do servidor Evolution API (ex: https://api.evolution.com)
            api_key: Chave de API para autenticação
            instance_name: Nome da instância do WhatsApp
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.instance_name = instance_name
        self.headers = {
            "Content-Type": "application/json",
            "apikey": api_key
        }
        self.success_count = 0
        self.failed_employees = []
        self.sent_employees = []
        self.status_manager = StatusManager("comunicados_status.json")
        self.sent_files_dir = "enviados_comunicados"
        
        # Criar diretório de arquivos enviados se não existir
        os.makedirs(self.sent_files_dir, exist_ok=True)
        
    def add_random_delay(self, base_delay=15, variation=5):
        """Adiciona delay aleatório para parecer mais humano"""
        delay = base_delay + random.uniform(-variation, variation)
        logging.info(f"Aguardando {delay:.1f} segundos...")
        time.sleep(delay)
    
    def format_phone_number(self, phone_number):
        """
        Formata o número de telefone para o padrão internacional
        Remove caracteres especiais e adiciona código do país se necessário
        """
        # Remove todos os caracteres não numéricos
        clean_number = ''.join(filter(str.isdigit, str(phone_number)))
        
        # Se não começar com código do país, assume Brasil (55)
        if not clean_number.startswith('55') and len(clean_number) >= 10:
            clean_number = '55' + clean_number
        
        # Adiciona o 9 no celular se necessário (padrão brasileiro)
        if len(clean_number) == 12 and clean_number[4] != '9':
            clean_number = clean_number[:4] + '9' + clean_number[4:]
        
        return clean_number
    
    def send_text_message(self, number, text, delay=0, retry_count=3):
        """Envia mensagem de texto usando Evolution API"""
        url = f"{self.server_url}/message/sendText/{self.instance_name}"
        
        payload = {
            "number": number,
            "text": text,
            "delay": delay
        }
        
        for attempt in range(retry_count):
            try:
                response = requests.post(url, headers=self.headers, json=payload, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                logging.info(f"Mensagem enviada com sucesso para {number}. ID: {result.get('key', {}).get('id', 'N/A')}")
                return True
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logging.error(f"Erro 401 Unauthorized - Verifique a API key")
                    return False
                elif e.response.status_code == 404:
                    logging.error(f"Erro 404 - Instância {self.instance_name} não encontrada")
                    return False
                elif e.response.status_code == 429:
                    logging.warning(f"Rate limit atingido. Aguardando 60 segundos...")
                    time.sleep(60)
                    continue
                else:
                    logging.error(f"Erro HTTP {e.response.status_code} ao enviar mensagem para {number}: {e}")
                    
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout na tentativa {attempt + 1} para {number}")
                if attempt < retry_count - 1:
                    time.sleep(10)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Erro de requisição ao enviar mensagem para {number}: {e}")
                
            except Exception as e:
                logging.error(f"Erro inesperado ao enviar mensagem para {number}: {e}")
            
            if attempt < retry_count - 1:
                logging.info(f"Tentativa {attempt + 1} falhou. Tentando novamente em 30 segundos...")
                time.sleep(30)
        
        return False
    
    def file_to_base64(self, file_path):
        """Converte arquivo para base64"""
        try:
            with open(file_path, "rb") as file:
                encoded_string = base64.b64encode(file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            logging.error(f"Erro ao converter arquivo para base64: {e}")
            return None
    
    def send_media_message(self, number, file_path, filename=None, caption=None, delay=0, retry_count=3):
        """Envia arquivo de mídia usando Evolution API"""
        url = f"{self.server_url}/message/sendMedia/{self.instance_name}"
        
        # Converte arquivo para base64
        base64_content = self.file_to_base64(file_path)
        if not base64_content:
            return False
        
        # Determina o tipo de mídia baseado na extensão
        file_extension = os.path.splitext(file_path)[1].lower()
        media_type_map = {
            '.pdf': 'document',
            '.doc': 'document',
            '.docx': 'document',
            '.xls': 'document',
            '.xlsx': 'document',
            '.txt': 'document',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.mp4': 'video',
            '.avi': 'video',
            '.mov': 'video',
            '.mp3': 'audio',
            '.wav': 'audio',
            '.ogg': 'audio'
        }
        
        media_type = media_type_map.get(file_extension, 'document')
        
        payload = {
            "number": number,
            "mediatype": media_type,
            "mimetype": mimetypes.guess_type(file_path)[0] or "application/octet-stream",
            "caption": caption or "",
            "media": base64_content,
            "fileName": filename or os.path.basename(file_path),
            "delay": delay
        }
        
        for attempt in range(retry_count):
            try:
                response = requests.post(url, headers=self.headers, json=payload, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                logging.info(f"Mídia enviada com sucesso para {number}. ID: {result.get('key', {}).get('id', 'N/A')}")
                return True
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logging.error(f"Erro 401 Unauthorized - Verifique a API key")
                    return False
                elif e.response.status_code == 404:
                    logging.error(f"Erro 404 - Instância {self.instance_name} não encontrada")
                    return False
                elif e.response.status_code == 413:
                    logging.error(f"Arquivo muito grande para {number}. Pulando...")
                    return False
                elif e.response.status_code == 429:
                    logging.warning(f"Rate limit atingido. Aguardando 120 segundos...")
                    time.sleep(120)
                    continue
                else:
                    logging.error(f"Erro HTTP {e.response.status_code} ao enviar mídia para {number}: {e}")
                    
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout na tentativa {attempt + 1} para envio de mídia para {number}")
                if attempt < retry_count - 1:
                    time.sleep(20)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Erro de requisição ao enviar mídia para {number}: {e}")
                
            except Exception as e:
                logging.error(f"Erro inesperado ao enviar mídia para {number}: {e}")
            
            if attempt < retry_count - 1:
                logging.info(f"Tentativa {attempt + 1} falhou. Tentando novamente em 60 segundos...")
                time.sleep(60)
        
        return False
    
    def check_instance_status(self):
        """Verifica o status da instância"""
        url = f"{self.server_url}/instance/connectionState/{self.instance_name}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            # A partir da v2.2.2, o status pode vir em 'state' ou 'status'
            status = result.get('instance', {}).get('state', result.get('instance', {}).get('status', 'unknown'))
            logging.info(f"Status da instância {self.instance_name}: {status}")
            
            if status != 'open' and status != 'connected': # Adicionado 'connected' para v2.2.2+
                logging.warning(f"Instância não está conectada. Status: {status}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao verificar status da instância: {e}")
            return False
    
    def process_employee(self, colaborador, comunicado_path, mensagem):
        """Processa um colaborador individual"""
        employee_name = colaborador["Nome"]
        phone_number = str(colaborador["Telefone"])
        setor = colaborador.get("Setor", "N/A")
        obra = colaborador.get("Obra", "N/A")
        
        # Usar nome como ID único para comunicados (diferente dos holerites que usam ID_Unico)
        unique_id = f"{employee_name}_{phone_number}"

        # Atualiza status para "processando"
        self.status_manager.update_current_step(f"Processando {employee_name}", employee_name)
        self.status_manager.update_employee_status(unique_id, employee_name, phone_number, "processing", "Iniciando processamento")

        if phone_number == "nan" or not phone_number.strip():
            logging.warning(f"Número de telefone inválido para {employee_name}. Pulando...")
            self.failed_employees.append({"nome": employee_name, "motivo": "Telefone inválido"})
            self.status_manager.update_employee_status(unique_id, employee_name, phone_number, "failed", "Telefone inválido")
            return False

        # Formatar número de telefone
        formatted_phone = self.format_phone_number(phone_number)
        
        logging.info(f"Iniciando envio para {employee_name} (Setor: {setor}, Obra: {obra}) no número {formatted_phone}...")

        # Mensagem personalizada com informações do colaborador
        personalized_message = f"{mensagem}"
        
        # Enviar mensagem de texto se houver
        if mensagem.strip():
            self.status_manager.update_employee_status(unique_id, employee_name, formatted_phone, "processing", "Enviando mensagem")
            if not self.send_text_message(formatted_phone, personalized_message):
                logging.error(f"Falha ao enviar mensagem para {employee_name}")
                self.failed_employees.append({"nome": employee_name, "motivo": "Falha na mensagem"})
                self.status_manager.update_employee_status(unique_id, employee_name, formatted_phone, "failed", "Falha na mensagem")
                return False
            # Delay entre mensagem e arquivo, se ambos existirem
            if comunicado_path and os.path.exists(comunicado_path):
                self.add_random_delay(20, 8)

        # Envio do comunicado (arquivo) se houver
        if comunicado_path and os.path.exists(comunicado_path):
            self.status_manager.update_employee_status(unique_id, employee_name, formatted_phone, "processing", "Enviando comunicado")
            filename = os.path.basename(comunicado_path)
            if not self.send_media_message(formatted_phone, comunicado_path, filename, caption=personalized_message if not (mensagem and mensagem.strip()) else None):
                logging.error(f"Falha ao enviar comunicado para {employee_name}")
                self.failed_employees.append({"nome": employee_name, "motivo": "Falha no envio do comunicado"})
                self.status_manager.update_employee_status(unique_id, employee_name, formatted_phone, "failed", "Falha no envio do comunicado")
                return False
        
        # Se nem mensagem nem comunicado foram enviados, é um erro
        if not mensagem.strip() and (not comunicado_path or not os.path.exists(comunicado_path)):
            logging.error(f"Nenhuma mensagem ou comunicado para enviar para {employee_name}")
            self.failed_employees.append({"nome": employee_name, "motivo": "Nenhum conteúdo para enviar"})
            self.status_manager.update_employee_status(unique_id, employee_name, formatted_phone, "failed", "Nenhum conteúdo para enviar")
            return False

        self.success_count += 1
        self.sent_employees.append({"nome": employee_name, "telefone": formatted_phone, "setor": setor, "obra": obra})
        self.status_manager.update_employee_status(unique_id, employee_name, formatted_phone, "success", "Comunicado enviado com sucesso")
        
        logging.info(f"✅ Processo completo para {employee_name}!")
        
        return True

    def send_comunicados_to_api(self, colaboradores_data, comunicado_path, mensagem):
        """Função principal para envio dos comunicados"""
        
        # Verificar se já há uma execução em andamento
        if self.status_manager.is_running():
            logging.error("Já existe uma execução em andamento. Aguarde a conclusão ou resete o status.")
            return
        
        # Verificar status da instância antes de começar
        if not self.check_instance_status():
            logging.error("Instância não está conectada. Abortando envio.")
            return
        
        # Verificar se o arquivo de comunicado existe, se um caminho foi fornecido
        if comunicado_path and not os.path.exists(comunicado_path):
            logging.error(f"Arquivo de comunicado não encontrado: {comunicado_path}")
            return

        total_employees = len(colaboradores_data)
        execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Iniciar execução
        if not self.status_manager.start_execution(total_employees, execution_id):
            logging.error("Não foi possível iniciar a execução. Verifique se não há outra execução em andamento.")
            return
        
        logging.info(f"Iniciando o envio de comunicados para {total_employees} colaboradores usando Evolution API v2.2.2.")
        logging.info(f"Instância: {self.instance_name}")
        logging.info(f"Arquivo: {comunicado_path}")
        logging.info(f"ID da execução: {execution_id}")

        try:
            for index, colaborador in enumerate(colaboradores_data):
                logging.info(f"\n--- Processando colaborador {index + 1}/{total_employees} ---")
                
                success = self.process_employee(colaborador, comunicado_path, mensagem)
                
                # Delay entre funcionários (mais longo para evitar spam)
                if index < total_employees - 1:  # Não fazer delay no último
                    self.add_random_delay(30, 10)  # Delay maior entre colaboradores
                
        except KeyboardInterrupt:
            logging.warning("Execução interrompida pelo usuário")
        except Exception as e:
            logging.error(f"Erro durante a execução: {e}")
        finally:
            # Finalizar execução
            self.status_manager.end_execution()
            
            # Mover arquivo de comunicado para pasta 'enviados' se houve pelo menos um sucesso
            if self.success_count > 0:
                try:
                    filename = os.path.basename(comunicado_path)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_filename = f"{timestamp}_{filename}"
                    destination_path = os.path.join(self.sent_files_dir, new_filename)
                    shutil.copy2(comunicado_path, destination_path)
                    logging.info(f"Arquivo de comunicado copiado para 'enviados': {new_filename}")
                except Exception as e:
                    logging.error(f"Erro ao copiar arquivo para 'enviados': {e}")

        # Relatório final
        logging.info(f"\n=== RELATÓRIO FINAL ===")
        logging.info(f"Total de colaboradores processados: {total_employees}")
        logging.info(f"Envios bem-sucedidos: {self.success_count}")
        logging.info(f"Envios falharam: {len(self.failed_employees)}")
        
        if self.failed_employees:
            logging.info("\nColaboradores que falharam:")
            for emp in self.failed_employees:
                logging.info(f"- {emp['nome']}: {emp['motivo']}")
        
        if self.sent_employees:
            logging.info("\nColaboradores que receberam o comunicado:")
            for emp in self.sent_employees:
                logging.info(f"- {emp['nome']} ({emp['setor']}/{emp['obra']}): {emp['telefone']}")

def main():
    """Função principal"""
    # Carregar dados temporários
    try:
        with open('temp_comunicado_data.json', 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
    except FileNotFoundError:
        logging.error("Arquivo de dados temporários não encontrado. Execute pelo app Streamlit.")
        return
    except Exception as e:
        logging.error(f"Erro ao carregar dados temporários: {e}")
        return
    
    # Configurações da Evolution API (carregadas do .env)
    server_url = os.getenv("EVOLUTION_SERVER_URL")
    api_key = os.getenv("EVOLUTION_API_KEY") 
    instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
    
    if not all([server_url, api_key, instance_name]):
        logging.error("Configurações da Evolution API não encontradas no arquivo .env")
        logging.error("Certifique-se de definir: EVOLUTION_SERVER_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_NAME")
        return
    
    # Criar instância do sender
    sender = ComunicadosSenderEvolution(server_url, api_key, instance_name)
    
    # Executar envio
    sender.send_comunicados_to_api(
        temp_data['colaboradores'],
        temp_data['comunicado_path'],
        temp_data['mensagem']
    )
    
    # Limpar arquivo temporário
    try:
        os.remove('temp_comunicado_data.json')
    except:
        pass

if __name__ == "__main__":
    main()