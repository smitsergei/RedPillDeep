#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSH deployment script for Ubuntu server"""
import paramiko
import sys
import os
from pathlib import Path

# Установка кодировки для Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "45.12.109.193"
USER = "root"
PASSWORD = "7sQD6PurjHWy"
REMOTE_PATH = "/root/redpilldeep"
LOCAL_PATH = r"D:\code\redpiildeep\RedPillDeep"

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    return client

def execute_command(client, command):
    print(f"   $ {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    output = stdout.read().decode()
    error = stderr.read().decode()
    exit_status = stdout.channel.recv_exit_status()
    if output:
        for line in output.split('\n')[:20]:  # Ограничим вывод
            if line.strip():
                print(f"   {line}")
    if error and exit_status != 0:
        print(f"   ERROR: {error}")
    return exit_status

def upload_directory(sftp, local_dir, remote_dir):
    """Рекурсивная загрузка директории"""
    local_dir = Path(local_dir)
    for item in local_dir.iterdir():
        if item.is_file():
            remote_file = f"{remote_dir}/{item.name}"
            # Пропускаем служебные файлы
            if item.name.startswith('.'):
                continue
            print(f"   ↑ {item.name}")
            sftp.put(str(item), remote_file)
        elif item.is_dir():
            remote_subdir = f"{remote_dir}/{item.name}"
            try:
                sftp.mkdir(remote_subdir)
            except:
                pass
            upload_directory(sftp, item, remote_subdir)

def main():
    print(f"=== Деплой на сервер {HOST} ===\n")

    try:
        client = create_ssh_client()
        sftp = client.open_sftp()
        print("Подключено!\n")

        # 1. Установка docker-compose
        print("=== Установка docker-compose ===")
        execute_command(client, "apt-get update")
        execute_command(client, "apt-get install -y docker-compose")

        # 2. Создание директории
        print("\n=== Создание директории проекта ===")
        execute_command(client, f"mkdir -p {REMOTE_PATH}")
        execute_command(client, f"rm -rf {REMOTE_PATH}/*")

        # 3. Загрузка файлов
        print("\n=== Загрузка файлов проекта ===")
        files_to_upload = [
            "Dockerfile",
            "docker-compose.yml",
            "requirements.txt",
            "main.py",
            ".env",
            "agents/",
            "core/",
            "tools/",
            "tg_bot.py"
        ]

        for item in files_to_upload:
            local_item = Path(LOCAL_PATH) / item
            if local_item.is_file():
                print(f"   {item}")
                sftp.put(str(local_item), f"{REMOTE_PATH}/{item}")
            elif local_item.is_dir():
                print(f"   {item}/")
                try:
                    sftp.mkdir(f"{REMOTE_PATH}/{item}")
                except:
                    pass
                upload_directory(sftp, local_item, f"{REMOTE_PATH}/{item}")

        sftp.close()

        # 4. Сборка и запуск Docker
        print("\n=== Сборка Docker образа ===")
        execute_command(client, f"cd {REMOTE_PATH} && docker-compose build")

        print("\n=== Запуск контейнера ===")
        execute_command(client, f"cd {REMOTE_PATH} && docker-compose up -d")

        print("\n=== Статус контейнеров ===")
        execute_command(client, "docker ps")

        print("\n=== Логи (последние 30 строк) ===")
        execute_command(client, "docker logs --tail 30 $(docker ps -q -f name=redpill) 2>/dev/null || echo 'Нет активных контейнеров'")

        client.close()
        print("\n=== Деплой завершен! ===")

    except paramiko.AuthenticationException:
        print("Ошибка аутентификации")
    except paramiko.SSHException as e:
        print(f"SSH ошибка: {e}")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
