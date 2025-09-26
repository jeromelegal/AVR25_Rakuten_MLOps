#!/usr/bin/env python3
import yaml
import subprocess
from pathlib import Path

class VMConfigurator:
    def __init__(self):
        self.yaml_file = "/mnt/user-data"

    def log(self, level, message):
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARN": "\033[1;33m",
            "ERROR": "\033[0;31m"
        }
        color = colors.get(level, "\033[0m")
        print(f"{color}[{level}] {message}\033[0m")

    def run_command(self, command, check=True):
        try:
            result = subprocess.run(command, shell=True, check=check,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.log("ERROR", f"Command failed: {e.stderr}")
            return None

    def configure_dns(self):
        """Configure les serveurs DNS"""
        self.log("INFO", "Configuration des serveurs DNS...")
        dns_config = "nameserver 8.8.8.8\nnameserver 8.8.4.4"
        try:
            with open("/etc/resolv.conf", "w") as f:
                f.write(dns_config)
            return True
        except Exception as e:
            self.log("ERROR", f"Erreur configuration DNS: {e}")
            return False

    def install_package(self, package):
        """Installe un paquet"""
        self.log("INFO", f"Installation de {package}...")
        try:
            self.run_command(f"apt-get install -y {package}", check=True)
            return True
        except Exception as e:
            self.log("ERROR", f"Erreur installation {package}: {e}")
            return False

    def load_config(self):
        """Charge la configuration depuis le YAML"""
        try:
            with open(self.yaml_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.log("ERROR", f"Erreur lecture YAML: {e}")
            return None

    def configure_hostname(self, config):
        """Configure le nom d'hôte"""
        hostname = config.get('autoinstall', {}).get('identity', {}).get('hostname')
        if not hostname:
            self.log("WARN", "Aucun nom d'hôte spécifié")
            return True
        self.log("INFO", f"Configuration du nom d'hôte à {hostname}...")
        try:
            # Essayer d'abord avec hostnamectl
            if self.run_command(f"hostnamectl set-hostname {hostname}", check=False) is None:
                with open("/etc/hostname", "w") as f:
                    f.write(hostname + "\n")
            # Mettre à jour /etc/hosts
            with open("/etc/hosts", "r") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                if line.startswith("127.0.1.1"):
                    new_lines.append(f"127.0.1.1 {hostname}\n")
                else:
                    new_lines.append(line)
            if not any(line.startswith("127.0.1.1") for line in lines):
                new_lines.append(f"127.0.1.1 {hostname}\n")
            with open("/etc/hosts", "w") as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            self.log("ERROR", f"Erreur configuration hostname: {e}")
            return False

    def configure_network(self, config):
        """Configure le réseau en copiant directement depuis le YAML"""
        network_config = config.get('autoinstall', {}).get('network', {})
        if not network_config:
            self.log("WARN", "Aucune configuration réseau trouvée")
            return True
        try:
            # Écrire la configuration réseau directement dans le fichier netplan
            with open("/etc/netplan/50-cloud-init.yaml", "w") as f:
                yaml.dump({'network': network_config}, f, sort_keys=False)
            # Appliquer la configuration
            self.run_command("netplan apply", check=True)
            return True
        except Exception as e:
            self.log("ERROR", f"Erreur configuration réseau: {e}")
            return False

    def configure_user(self, config):
        """Configure l'utilisateur"""
        identity = config.get('autoinstall', {}).get('identity', {})
        username = identity.get('username')
        password = identity.get('password')
        if not username:
            self.log("WARN", "Aucun utilisateur spécifié")
            return True
        try:
            if not self.run_command(f"id {username}", check=False):
                self.run_command(f"useradd -m {username}", check=True)
            if password:
                self.run_command(f"echo '{username}:{password}' | chpasswd", check=True)
            return True
        except Exception as e:
            self.log("ERROR", f"Erreur configuration utilisateur: {e}")
            return False

    def configure_sudo(self, config):
        """Configure les permissions sudo pour l'utilisateur"""
        identity = config.get('autoinstall', {}).get('identity', {})
        username = identity.get('username', 'ubuntu')  # Default to 'ubuntu' if not specified
        sudoers_line = f"{username} ALL=(ALL) NOPASSWD:ALL"
        sudoers_file = f"/etc/sudoers.d/{username}"
        try:
            # Écrire la configuration sudoers dans un fichier dans /etc/sudoers.d/
            with open(sudoers_file, "w") as f:
                f.write(sudoers_line + "\n")
            # Définir les permissions appropriées
            self.run_command(f"chmod 440 {sudoers_file}", check=True)
            return True
        except Exception as e:
            self.log("ERROR", f"Erreur configuration sudo: {e}")
            return False

    def install_packages(self, config):
        """Installe les paquets spécifiés"""
        packages = config.get('autoinstall', {}).get('packages', [])
        if not packages:
            self.log("WARN", "Aucun paquet spécifié")
            return True
        for pkg in packages:
            self.install_package(pkg)
        return True

    def resize_partition(self, config):
        """Redimensionne la partition pour utiliser tout l'espace disponible sur le disque"""
        resize_config = config.get('autoinstall', {}).get('resize_partition', {})
        if not resize_config.get('enable', False):
            self.log("INFO", "Redimensionnement de la partition désactivé.")
            return True
        partition = resize_config.get('partition', '/dev/vda3')
        disk = resize_config.get('disk', '/dev/vda')
        self.log("INFO", f"Redimensionnement de la partition {partition}...")
        # Vérifier si l'utilisateur est root
        if self.run_command("id -u", check=False) != "0":
            self.log("ERROR", "Ce script doit être exécuté en tant que root.")
            return False
        # Vérifier le type de système de fichiers
        fs_type = self.run_command(f"lsblk -no FSTYPE {partition}", check=False)
        self.log("INFO", f"Type de système de fichiers : {fs_type}")
        # Vérifier si la partition est montée
        mount_info = self.run_command("mount", check=False)
        if partition in mount_info:
            self.log("ERROR", f"La partition {partition} est actuellement montée. Le redimensionnement ne peut pas être effectué.")
            return False
        try:
            # Utiliser growpart pour redimensionner la partition
            self.log("INFO", f"Redimensionnement de la partition {partition} avec growpart...")
            result = self.run_command(f"growpart {disk} 3", check=True)
            self.log("INFO", f"Résultat de growpart : {result}")
            # Redimensionner le système de fichiers
            if 'ext4' in fs_type:
                self.log("INFO", "Redimensionnement du système de fichiers ext4...")
                result = self.run_command(f"resize2fs {partition}", check=True)
                self.log("INFO", f"Résultat du redimensionnement : {result}")
            elif 'xfs' in fs_type:
                self.log("INFO", "Redimensionnement du système de fichiers xfs...")
                result = self.run_command(f"xfs_growfs {partition}", check=True)
                self.log("INFO", f"Résultat du redimensionnement : {result}")
            else:
                self.log("ERROR", "Type de système de fichiers non pris en charge.")
                return False
            self.log("SUCCESS", "Partition redimensionnée avec succès.")
            return True
        except Exception as e:
            self.log("ERROR", f"Une erreur est survenue : {e}")
            return False

    def resize_logical_volume(self, config):
        """Redimensionne le volume logique pour utiliser tout l'espace disponible sur le disque"""
        resize_config = config.get('autoinstall', {}).get('resize_logical_volume', {})
        if not resize_config.get('enable', False):
            self.log("INFO", "Redimensionnement du volume logique désactivé.")
            return True
        self.log("INFO", "Redimensionnement du volume logique...")
        # Vérifier si l'utilisateur est root
        if self.run_command("id -u", check=False) != "0":
            self.log("ERROR", "Ce script doit être exécuté en tant que root.")
            return False
        try:
            # Redimensionner le volume physique (PV)
            self.log("INFO", "Redimensionnement du volume physique (PV)...")
            result = self.run_command("pvresize /dev/vda3", check=True)
            self.log("INFO", f"Résultat de pvresize : {result}")
            # Redimensionner le volume logique (LV)
            self.log("INFO", "Redimensionnement du volume logique (LV)...")
            result = self.run_command("lvextend -l +100%FREE /dev/mapper/ubuntu--vg-ubuntu--lv", check=True)
            self.log("INFO", f"Résultat de lvextend : {result}")
            # Redimensionner le système de fichiers
            self.log("INFO", "Redimensionnement du système de fichiers...")
            result = self.run_command("resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv", check=True)
            self.log("INFO", f"Résultat du redimensionnement du système de fichiers : {result}")
            self.log("SUCCESS", "Volume logique redimensionné avec succès.")
            return True
        except Exception as e:
            self.log("ERROR", f"Une erreur est survenue : {e}")
            return False

    def main(self):
        self.log("INFO", "Début de la configuration de la VM")
        # Charger la configuration
        config = self.load_config()
        if not config:
            return
        # Configurer les composants
        self.configure_dns()
        self.configure_hostname(config)
        self.configure_network(config)
        self.configure_user(config)
        self.configure_sudo(config)  # Ajout de la configuration sudo
        self.install_packages(config)
        self.resize_partition(config)
        self.resize_logical_volume(config)
        self.log("SUCCESS", "Configuration terminée")

if __name__ == "__main__":
    configurator = VMConfigurator()
    configurator.main()
