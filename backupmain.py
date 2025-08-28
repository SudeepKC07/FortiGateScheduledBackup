# latest change date: 2025-08-28
import csv
import requests
import os
from io import StringIO
from datetime import datetime
from netmiko import ConnectHandler

# ===== CSV URL =====
csv_url = "https://raw.githubusercontent.com/SudeepKC07/DeviceLists/main/DeviceLists/fortigates.csv"

# ===== TFTP Server IP =====
tftp_server_ip = "192.168.209.66"  # your laptop IP where TFTP server is running

# ===== Functions =====
def log_message(message):
    """Print and log message with timestamp"""
    log_file = "backup_log.txt"
    timestamped_msg = f"{datetime.now()} - {message}"
    print(timestamped_msg)
    with open(log_file, "a") as f:
        f.write(timestamped_msg + "\n")

def backup_fortigate(device):
    """Backup a single FortiGate device to TFTP server"""
    device_name = device["DEV"]

    try:
        log_message(f"[INFO] Connecting to {device['host']} ({device_name})")
        connection = ConnectHandler(
            device_type="fortinet",
            host=device["host"],
            username=device["username"],
            password=device["password"],
            port=int(device["port"]),
            fast_cli=False
        )

        prompt = connection.find_prompt()
        log_message(f"[DEBUG] Detected prompt: {prompt}")

        # Build filename for TFTP
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        tftp_filename = f"{device_name}_backup_{timestamp}.cfg"

        # Execute backup to TFTP
        cmd = f"execute backup config tftp {tftp_filename} {tftp_server_ip}"
        output = connection.send_command_timing(cmd, delay_factor=2)

        if "backup failed" in output.lower() or "error" in output.lower():
            log_message(f"[ERROR] Backup failed for {device_name} ({device['host']}) - {output}")
        else:
            log_message(f"[SUCCESS] Backup sent to TFTP for {device_name} -> {tftp_filename}")

        connection.disconnect()

    except Exception as e:
        log_message(f"[ERROR] Failed backup for {device['host']} ({device_name}) - {e}")

def fetch_devices_from_github(url):
    """Fetch device list from GitHub CSV"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_data = response.content.decode("utf-8-sig")  # handle BOM
        reader = csv.DictReader(StringIO(csv_data))
        devices = []
        for row in reader:
            devices.append({
                "host": row["host"],
                "username": row["username"],
                "password": row["password"],
                "port": row.get("port", 22),
                "DEV": row.get("DEV", "Unknown")
            })
        return devices
    except Exception as e:
        log_message(f"[ERROR] Could not fetch devices from GitHub: {e}")
        return []

# ===== Main =====
if __name__ == "__main__":

    
    devices = fetch_devices_from_github(csv_url)
    if not devices:
        log_message("[ERROR] No devices found. Exiting.")
    else:
        for device in devices:
            backup_fortigate(device)
