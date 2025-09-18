"""
Модуль синхронизации с облачными сервисами
"""

import os
import json
import ftplib
import smtplib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import zipfile

class CloudSyncConfig:
    """Конфигурация облачной синхронизации"""
    
    def __init__(self, config_file: str = "cloud_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Загрузка конфигурации"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
        
        return self.get_default_config()
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def get_default_config(self) -> dict:
        """Конфигурация по умолчанию"""
        return {
            "enabled": False,
            "sync_method": "ftp",  # ftp, google_drive, email, webhook
            "auto_sync": True,
            "sync_schedule": "daily",  # immediate, daily, weekly
            "ftp": {
                "host": "",
                "port": 21,
                "username": "",
                "password": "",
                "remote_path": "/reports/"
            },
            "google_drive": {
                "credentials_file": "",
                "folder_id": ""
            },
            "email": {
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": []
            },
            "webhook": {
                "url": "",
                "headers": {},
                "auth_token": ""
            }
        }

class FTPUploader:
    """Загрузчик файлов на FTP сервер"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def upload_file(self, local_path: str, remote_filename: str = None) -> bool:
        """Загрузка файла на FTP"""
        try:
            if not remote_filename:
                remote_filename = Path(local_path).name
            
            with ftplib.FTP() as ftp:
                ftp.connect(self.config['host'], self.config['port'])
                ftp.login(self.config['username'], self.config['password'])
                
                # Переходим в нужную папку
                try:
                    ftp.cwd(self.config['remote_path'])
                except:
                    # Создаем папку если не существует
                    self._create_remote_dirs(ftp, self.config['remote_path'])
                    ftp.cwd(self.config['remote_path'])
                
                # Загружаем файл
                with open(local_path, 'rb') as file:
                    ftp.storbinary(f'STOR {remote_filename}', file)
                
                print(f"✅ Файл {remote_filename} загружен на FTP")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка загрузки на FTP: {e}")
            return False
    
    def _create_remote_dirs(self, ftp, path: str):
        """Создание удаленных директорий"""
        dirs = path.strip('/').split('/')
        for dir_name in dirs:
            if dir_name:
                try:
                    ftp.mkd(dir_name)
                except:
                    pass  # Папка уже существует
                try:
                    ftp.cwd(dir_name)
                except:
                    pass

class EmailSender:
    """Отправка отчетов по email"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def send_report(self, file_path: str, project_name: str = "Объект") -> bool:
        """Отправка отчета по email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['username']
            msg['To'] = ', '.join(self.config['recipients'])
            msg['Subject'] = f"Отчет по дефектам - {project_name} - {datetime.now().strftime('%d.%m.%Y')}"
            
            # Добавляем файл как вложение
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {Path(file_path).name}'
            )
            msg.attach(part)
            
            # Отправляем email
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['username'], self.config['password'])
                server.send_message(msg)
            
            print(f"✅ Отчет отправлен по email: {', '.join(self.config['recipients'])}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            return False

class WebhookSender:
    """Отправка отчетов через Webhook"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def send_report(self, file_path: str, project_name: str = "Объект") -> bool:
        """Отправка отчета через Webhook"""
        try:
            import requests
            
            # Подготавливаем данные
            files = {'file': open(file_path, 'rb')}
            data = {
                'project_name': project_name,
                'timestamp': datetime.now().isoformat(),
                'file_type': 'defect_report'
            }
            
            headers = self.config.get('headers', {})
            if self.config.get('auth_token'):
                headers['Authorization'] = f"Bearer {self.config['auth_token']}"
            
            # Отправляем POST запрос
            response = requests.post(
                self.config['url'],
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Отчет отправлен через Webhook: {response.status_code}")
                return True
            else:
                print(f"❌ Ошибка Webhook: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка отправки Webhook: {e}")
            return False
        finally:
            try:
                files['file'].close()
            except:
                pass

class GoogleDriveUploader:
    """Загрузчик в Google Drive"""
    
    def __init__(self, config: dict):
        self.config = config
        self.service = None
    
    def authenticate(self) -> bool:
        """Аутентификация в Google Drive"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            creds = None
            token_file = Path('token.json')
            
            if token_file.exists():
                creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config['credentials_file'], SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            print(f"❌ Ошибка аутентификации Google Drive: {e}")
            return False
    
    def upload_file(self, file_path: str, folder_id: str = None) -> bool:
        """Загрузка файла в Google Drive"""
        try:
            if not self.service and not self.authenticate():
                return False
            
            from googleapiclient.http import MediaFileUpload
            
            file_metadata = {
                'name': Path(file_path).name,
                'parents': [folder_id or self.config['folder_id']] if folder_id or self.config['folder_id'] else None
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f"✅ Файл загружен в Google Drive: {file.get('id')}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки в Google Drive: {e}")
            return False

class CloudSyncManager:
    """Менеджер облачной синхронизации"""
    
    def __init__(self, config_file: str = None):
        self.config_manager = CloudSyncConfig(config_file or "cloud_config.json")
        self.uploaders = {}
        self._init_uploaders()
    
    def _init_uploaders(self):
        """Инициализация загрузчиков"""
        config = self.config_manager.config
        
        if config.get('ftp', {}).get('host'):
            self.uploaders['ftp'] = FTPUploader(config['ftp'])
        
        if config.get('email', {}).get('smtp_server'):
            self.uploaders['email'] = EmailSender(config['email'])
        
        if config.get('webhook', {}).get('url'):
            self.uploaders['webhook'] = WebhookSender(config['webhook'])
        
        if config.get('google_drive', {}).get('credentials_file'):
            self.uploaders['google_drive'] = GoogleDriveUploader(config['google_drive'])
    
    def sync_file(self, file_path: str, project_name: str = "Объект") -> Dict[str, bool]:
        """Синхронизация файла с облаком"""
        config = self.config_manager.config
        
        if not config.get('enabled', False):
            return {'status': False, 'message': 'Синхронизация отключена'}
        
        results = {}
        sync_method = config.get('sync_method', 'ftp')
        
        if sync_method in self.uploaders:
            uploader = self.uploaders[sync_method]
            
            if sync_method == 'ftp':
                success = uploader.upload_file(file_path)
            elif sync_method == 'email':
                success = uploader.send_report(file_path, project_name)
            elif sync_method == 'webhook':
                success = uploader.send_report(file_path, project_name)
            elif sync_method == 'google_drive':
                success = uploader.upload_file(file_path)
            else:
                success = False
            
            results[sync_method] = success
        else:
            results['error'] = f"Загрузчик {sync_method} не настроен"
        
        return results
    
    def sync_project_reports(self, project_dir: Path, project_name: str) -> Dict[str, List]:
        """Синхронизация всех отчетов объекта"""
        reports_dir = project_dir / "reports"
        
        if not reports_dir.exists():
            return {'synced': [], 'failed': []}
        
        synced = []
        failed = []
        
        for report_file in reports_dir.glob("*.docx"):
            result = self.sync_file(str(report_file), project_name)
            
            if any(result.values()):
                synced.append(str(report_file))
            else:
                failed.append(str(report_file))
        
        return {'synced': synced, 'failed': failed}
    
    def create_project_archive(self, project_dir: Path, project_name: str) -> str:
        """Создание архива объекта для выгрузки"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{project_name}_{timestamp}.zip"
        archive_path = project_dir.parent / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_dir.parent)
                    zipf.write(file_path, arcname)
        
        return str(archive_path)
    
    def test_connection(self, sync_method: str = None) -> bool:
        """Тестирование соединения с облаком"""
        config = self.config_manager.config
        method = sync_method or config.get('sync_method', 'ftp')
        
        try:
            if method == 'ftp' and 'ftp' in self.uploaders:
                ftp_config = config['ftp']
                with ftplib.FTP() as ftp:
                    ftp.connect(ftp_config['host'], ftp_config['port'])
                    ftp.login(ftp_config['username'], ftp_config['password'])
                    return True
            
            elif method == 'email' and 'email' in self.uploaders:
                email_config = config['email']
                with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                    server.starttls()
                    server.login(email_config['username'], email_config['password'])
                    return True
            
            elif method == 'webhook' and 'webhook' in self.uploaders:
                import requests
                response = requests.get(config['webhook']['url'], timeout=10)
                return response.status_code < 500
            
            elif method == 'google_drive' and 'google_drive' in self.uploaders:
                return self.uploaders['google_drive'].authenticate()
            
        except Exception as e:
            print(f"❌ Ошибка тестирования {method}: {e}")
            return False
        
        return False
    
    def get_sync_stats(self) -> Dict:
        """Получение статистики синхронизации"""
        # Здесь можно добавить логику подсчета синхронизированных файлов
        return {
            'total_synced': 0,
            'last_sync': None,
            'failed_syncs': 0
        }