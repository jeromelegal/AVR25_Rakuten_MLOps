#!/usr/bin/env python3
import yaml
import subprocess
from pathlib import Path
import os
import shutil

class VMConfigurator:
    def __init__(self):
        self.yaml_file = "/mnt/user-data"
        self.mount_point = "/mnt"

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

    def configure_dns(self, config):
        """Configure les serveurs DNS"""
        network_config = config.get('network', {})
        ethernets = network_config.get('ethernets', {})
        dns_servers = None

        # Extraire les serveurs DNS de la configuration réseau
        for interface in ethernets.values():
            nameservers = interface.get('nameservers', {}).get('addresses', [])
            if nameservers:
                dns_servers = nameservers
                break

        # Si non trouvé dans la config réseau, utiliser les valeurs par défaut
        if not dns_servers:
            dns_servers = ['8.8.8.8', '8.8.4.4']

        self.log("INFO", "Configuration des serveurs DNS...")
        dns_config = "\n".join(f"nameserver {server}" for server in dns_servers)
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
                data = yaml.safe_load(f)
                # Accéder à la configuration autoinstall
                autoinstall_config = data.get('autoinstall', {})
                return autoinstall_config
        except Exception as e:
            self.log("ERROR", f"Erreur lecture YAML: {e}")
            return None

    def configure_hostname(self, config):
        """Configure le nom d'hôte"""
        identity = config.get('identity', {})
        hostname = identity.get('hostname')
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
        """Configure le réseau"""
        network_config = config.get('network', {})
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
        identity = config.get('identity', {})
        users = [identity] if identity else []
        if not users:
            self.log("INFO", "Aucun utilisateur supplémentaire à configurer")
            return True

        for user in users:
            username = user.get('username')
            password = user.get('password')
            groups = []  # Les groupes ne sont pas spécifiés dans la nouvelle structure
            if not username:
                self.log("WARN", "Nom d'utilisateur non spécifié")
                continue

            try:
                if not self.run_command(f"id {username}", check=False):
                    self.run_command(f"useradd -m {username}", check=True)
                    # Ajouter aux groupes
                    for group in groups:
                        self.run_command(f"usermod -aG {group} {username}", check=True)
                if password:
                    self.run_command(f"echo '{username}:{password}' | chpasswd", check=True)
                self.log("SUCCESS", f"Utilisateur {username} configuré avec succès")
            except Exception as e:
                self.log("ERROR", f"Erreur configuration utilisateur {username}: {e}")
                return False
        return True

    def configure_sudo(self, config):
        """Configure les permissions sudo pour les utilisateurs"""
        identity = config.get('identity', {})
        users = [identity] if identity else []
        if not users:
            self.log("INFO", "Aucun utilisateur à configurer pour sudo")
            return True

        for user in users:
            username = user.get('username')
            if not username:
                continue

            sudoers_line = f"{username} ALL=(ALL) NOPASSWD:ALL"
            sudoers_file = f"/etc/sudoers.d/{username}"
            try:
                # Écrire la configuration sudoers dans un fichier dans /etc/sudoers.d/
                with open(sudoers_file, "w") as f:
                    f.write(sudoers_line + "\n")
                # Définir les permissions appropriées
                self.run_command(f"chmod 440 {sudoers_file}", check=True)
                self.log("SUCCESS", f"Permissions sudo configurées pour {username}")
            except Exception as e:
                self.log("ERROR", f"Erreur configuration sudo pour {username}: {e}")
                return False
        return True

    # def install_packages(self, config):
    #     """Installe les paquets spécifiés"""
    #     # Les paquets ne sont pas explicitement spécifiés dans la nouvelle structure
    #     # On installe les paquets de base pour le moment
    #     packages = ['nginx', 'docker.io', 'kubelet', 'kubeadm', 'kubectl']
    #     if not packages:
    #         self.log("INFO", "Aucun paquet à installer")
    #         return True

    #     for pkg in packages:
    #         self.install_package(pkg)
    #     return True

    def resize_partition(self, config):
        """Redimensionne la partition pour utiliser tout l'espace disponible sur le disque"""
        disk_config = self.get_disk_config(config)
        if not disk_config:
            self.log("INFO", "Aucune configuration de disque trouvée.")
            return True

        resize_config = disk_config.get('resize_config', {})
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
        disk_config = self.get_disk_config(config)
        if not disk_config:
            self.log("INFO", "Aucune configuration de disque trouvée.")
            return True

        resize_config = disk_config.get('resize_config', {})
        methods = resize_config.get('methods', {})
        if not methods.get('lvm', False):
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

    def get_disk_config(self, config):
        """Récupère la configuration du disque principal"""
        storage = config.get('storage', {})
        disks = storage.get('disks', [])
        if not disks:
            return None

        # Trouver le disque système (celui qui a mount_point: "/")
        for disk in disks:
            if disk.get('mount_point') == '/':
                return disk
        return None

    def configure_disks(self, config):
        """Configure les disques supplémentaires"""
        storage = config.get('storage', {})
        disks = storage.get('disks', [])
        if not disks:
            self.log("INFO", "Aucun disque supplémentaire à configurer")
            return True

        for disk in disks:
            disk_path = disk.get('path', '')
            mount_point = disk.get('mount_point', '')

            # Ignorer le disque système
            if mount_point == '/':
                continue

            if not disk_path:
                continue

            self.log("INFO", f"Configuration du disque {disk_path}...")
            try:
                # Vérifier si le disque existe
                if not Path(disk_path).exists():
                    self.log("WARN", f"Disque {disk_path} introuvable")
                    continue

                # Partitionner le disque
                self.log("INFO", f"Partitionnement du disque {disk_path}...")
                self.run_command(f"parted -s {disk_path} mktable msdos", check=True)
                self.run_command(f"parted -s {disk_path} mkpart primary ext4 1MiB 100%", check=True)

                # Formater la partition
                partition_path = f"{disk_path}1"
                self.log("INFO", f"Formatage de la partition {partition_path}...")
                self.run_command(f"mkfs.{disk.get('filesystem', 'ext4')} {partition_path}", check=True)

                # Créer le point de montage
                if not mount_point:
                    mount_point = '/mnt/' + os.path.basename(disk_path)
                self.log("INFO", f"Création du point de montage {mount_point}...")
                self.run_command(f"mkdir -p {mount_point}", check=True)

                # Monter la partition
                self.log("INFO", f"Montage de la partition {partition_path} sur {mount_point}...")
                self.run_command(f"mount {partition_path} {mount_point}", check=True)

                # Définir les permissions si spécifié
                permissions = disk.get('permissions')
                if permissions:
                    self.run_command(f"chmod {permissions} {mount_point}", check=True)

                # Ajouter au fstab pour le montage automatique
                self.log("INFO", f"Ajout de la partition au fstab...")
                with open("/etc/fstab", "a") as f:
                    f.write(f"{partition_path} {mount_point} {disk.get('filesystem', 'ext4')} defaults 0 2\n")

                self.log("SUCCESS", f"Disque {disk_path} configuré avec succès")
            except Exception as e:
                self.log("ERROR", f"Erreur configuration disque {disk_path}: {e}")
                return False
        return True

    def configure_services(self, config):
        """Configure les services à démarrer au boot"""
        # Les services ne sont pas explicitement spécifiés dans la nouvelle structure
        # On configure les services Kubernetes par défaut
        services = {
            'kubelet': True,
            'docker': True
        }

        if not services:
            self.log("INFO", "Aucun service à configurer")
            return True

        for service, enable in services.items():
            if enable:
                self.log("INFO", f"Activation du service {service}...")
                self.run_command(f"systemctl enable {service}", check=True)
                self.run_command(f"systemctl start {service}", check=True)
            else:
                self.log("INFO", f"Désactivation du service {service}...")
                self.run_command(f"systemctl disable {service}", check=True)
                self.run_command(f"systemctl stop {service}", check=True)
        return True

    def copy_files(self, config):
        """Copie les fichiers spécifiés"""
        # Les fichiers à copier ne sont pas dans la nouvelle structure autoinstall
        # On utilise la structure originale pour cette partie
        try:
            with open(self.yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            files = data.get('copy_files', [])
        except Exception as e:
            self.log("ERROR", f"Erreur lecture YAML pour copy_files: {e}")
            return False

        if not files:
            self.log("INFO", "Aucun fichier à copier")
            return True

        for file in files:
            source = file.get('source')
            destination = file.get('destination')
            if not source or not destination:
                self.log("WARN", "Source ou destination non spécifiée pour un fichier")
                continue

            try:
                # Vérifier si le fichier source existe dans l'ISO
                source_path = f"{self.mount_point}/{source}"
                if not Path(source_path).exists():
                    self.log("WARN", f"Fichier source {source_path} introuvable")
                    continue

                # Créer le répertoire de destination si nécessaire
                dest_dir = os.path.dirname(destination)
                if dest_dir:
                    self.run_command(f"mkdir -p {dest_dir}", check=True)

                # Copier le fichier
                shutil.copy2(source_path, destination)
                self.log("SUCCESS", f"Fichier {source} copié vers {destination}")
            except Exception as e:
                self.log("ERROR", f"Erreur copie fichier {source}: {e}")
                return False
        return True

    def execute_scripts(self, config):
        """Exécute les scripts post-installation"""
        # Les scripts ne sont pas dans la nouvelle structure autoinstall
        # On utilise la structure originale pour cette partie
        try:
            with open(self.yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            scripts = data.get('post_install_scripts', [])
        except Exception as e:
            self.log("ERROR", f"Erreur lecture YAML pour post_install_scripts: {e}")
            return False

        if not scripts:
            self.log("INFO", "Aucun script à exécuter")
            return True

        for script in scripts:
            script_path = f"{self.mount_point}/{script}"
            if not Path(script_path).exists():
                self.log("WARN", f"Script {script_path} introuvable")
                continue

            self.log("INFO", f"Exécution du script {script}...")
            try:
                self.run_command(f"chmod +x {script_path}", check=True)
                self.run_command(script_path, check=True)
                self.log("SUCCESS", f"Script {script} exécuté avec succès")
            except Exception as e:
                self.log("ERROR", f"Erreur exécution script {script}: {e}")
                return False
        return True

    def main(self):
        self.log("INFO", "Début de la configuration de la VM")

        # Charger la configuration
        config = self.load_config()
        if not config:
            return

        # Configurer les composants
        self.configure_dns(config)
        self.configure_hostname(config)
        self.configure_network(config)
        self.configure_user(config)
        self.configure_sudo(config)
        # self.install_packages(config)
        self.resize_partition(config)
        self.resize_logical_volume(config)
        self.configure_disks(config)
        self.configure_services(config)
        self.copy_files(config)
        self.execute_scripts(config)

        self.log("SUCCESS", "Configuration terminée")

if __name__ == "__main__":
    configurator = VMConfigurator()
    configurator.main()
