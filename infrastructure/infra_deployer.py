#!/usr/bin/env python3
import base64
import os
import yaml
import libvirt
import jinja2
import subprocess
import grp
import pwd
import time
import json
import base64
import threading

# from pathlib import Path
from typing import Dict, List #, Optional

# Chemins et constants
ISO_DIR = "/var/lib/libvirt/isos"
VM_IMAGES_DIR = "/var/lib/libvirt/images"
CLOUD_INIT_ISO_DIR = "/var/lib/libvirt/cloud_init_isos"
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")

# Initialiser Jinja2 pour les templates
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True
)

def decode_base64_fields(data):
    """
    Décode les champs en base64 dans un dictionnaire de manière récursive.
    """
    if isinstance(data, dict):
        decoded_dict = {}
        for key, value in data.items():
            if key in ['out-data', 'err-data'] and isinstance(value, str):
                try:
                    decoded_value = base64.b64decode(value).decode('utf-8')
                    decoded_dict[key] = decoded_value
                except (base64.binascii.Error, UnicodeDecodeError):
                    decoded_dict[key] = value
            else:
                decoded_dict[key] = decode_base64_fields(value)
        return decoded_dict
    elif isinstance(data, list):
        return [decode_base64_fields(item) for item in data]
    else:
        return data

class InfraDeployer:
    def __init__(self, yaml_file: str):
        self.yaml_file = yaml_file
        self.conn = None
        self._infra = None

    @property
    def infra(self):
        if self._infra is None:
            raise RuntimeError("L'infrastructure n'a pas été chargée. Appelez load_infra() d'abord.")
        return self._infra

    @infra.setter
    def infra(self, value):
        self._infra = value

    def check_prerequisites(self):
        """Vérifie les prérequis avant déploiement."""
        errors = []
        # 1. Vérifier les groupes utilisateur
        user_groups = [g.gr_name for g in grp.getgrall() if pwd.getpwuid(os.getuid()).pw_name in g.gr_mem]
        required_groups = ['kvm', 'libvirt']
        for group in required_groups:
            if group not in user_groups:
                errors.append(f"L'utilisateur doit être dans le groupe '{group}' (sudo usermod -aG {group} $USER)")
        # 2. Vérifier les répertoires
        for dir_path in [ISO_DIR, VM_IMAGES_DIR, CLOUD_INIT_ISO_DIR, SCRIPTS_DIR, FILES_DIR]:
            if not os.path.exists(dir_path):
                errors.append(f"Répertoire introuvable: {dir_path} (sudo mkdir -p {dir_path})")
            else:
                if not os.access(dir_path, os.W_OK):
                    errors.append(f"Permissions insuffisantes sur {dir_path} (sudo chown -R $USER:$USER {dir_path})")
        # 3. Vérifier que libvirtd est actif
        try:
            subprocess.run(['systemctl', 'is-active', 'libvirtd'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            errors.append("Le service libvirtd n'est pas actif (sudo systemctl start libvirtd)")
        # 4. Vérifier la connexion à libvirt
        try:
            self.conn = libvirt.open("qemu:///system")
            if self.conn is None:
                errors.append("Impossible de se connecter à libvirt (vérifiez les permissions)")
        except Exception as e:
            errors.append(f"Erreur de connexion à libvirt: {e}")

    def load_infra(self):
        """Charge et valide le fichier YAML."""
        with open(self.yaml_file, 'r') as f:
            self.infra = yaml.safe_load(f)
        self.validate()

    def validate(self):
        """Valide le fichier YAML."""
        errors = []
        # Vérifier que les ISO existent
        for vm in self.infra['vms']:
            if 'cloud_init' in vm and 'iso' in vm['cloud_init']:
                iso_path = os.path.join(ISO_DIR, vm['cloud_init']['iso'])
                if not os.path.exists(iso_path):
                    errors.append(f"ISO introuvable: {iso_path}")
        # Vérifier les VMs sources
        vm_names = {vm['name'] for vm in self.infra.get('vms', [])}
        existing_vms = {dom.name() for dom in self.conn.listAllDomains()}
        for vm in self.infra.get('vms', []):
            if 'clone_init' in vm:
                source_vm_name = vm['clone_init']['source_vm']
                if source_vm_name not in existing_vms and source_vm_name not in vm_names:
                    errors.append(f"VM source {source_vm_name} non définie dans le YAML ni trouvée dans libvirt (utilisé par {vm['name']})")
                elif source_vm_name in vm_names:
                    source_vm_index = next((i for i, v in enumerate(self.infra.get('vms', [])) if v['name'] == source_vm_name), None)
                    clone_vm_index = next((i for i, v in enumerate(self.infra.get('vms', [])) if v['name'] == vm['name']), None)
                    if source_vm_index is not None and clone_vm_index is not None and source_vm_index > clone_vm_index:
                        errors.append(f"VM source {source_vm_name} doit être définie avant la VM clonée {vm['name']} dans le YAML")
        # Vérifier les réseaux
        defined_networks = {net['name'] for net in self.infra.get('networks', [])}
        existing_networks = {net.name() for net in self.conn.listAllNetworks()}
        for vm in self.infra.get('vms', []):
            for net_config in vm.get('networks', []):
                network_name = net_config['name']
                if network_name not in defined_networks and network_name not in existing_networks:
                    errors.append(f"Réseau {network_name} non défini dans le YAML ni trouvé dans libvirt (utilisé par {vm['name']})")
        # Vérifier les scripts
        for vm in self.infra.get('vms', []):
            for script in vm.get('post_install_scripts', []):
                script_path = os.path.join(SCRIPTS_DIR, script)
                if not os.path.exists(script_path):
                    errors.append(f"Script introuvable: {script_path} (utilisé par {vm['name']})")
        if errors:
            raise ValueError("Erreurs de validation:\n" + "\n".join(f"  - {e}" for e in errors))

    def network_exists(self, name: str) -> bool:
        """Vérifie si un réseau existe."""
        networks = self.conn.listAllNetworks(0)
        return any(net.name() == name for net in networks)

    def network_is_active(self, name: str) -> bool:
        """Vérifie si un réseau est actif."""
        networks = self.conn.listAllNetworks()
        for net in networks:
            if net.name() == name:
                return net.isActive()
        return False

    def vm_exists(self, name: str) -> bool:
        """Vérifie si une VM existe."""
        domains = self.conn.listAllDomains(0)
        for domain in domains:
            if domain.name() == name:
                return True
        return False

    def create_network(self, network: Dict):
        """Crée un réseau."""
        if self.network_exists(network['name']):
            print(f"  ! Réseau {network['name']} existe déjà, ignoré")
            return
        template = env.get_template('network.xml.j2')
        network_xml = template.render(network=network, netmask=netmask)
        try:
            self.conn.networkDefineXML(network_xml)
            print(f"  ✓ Réseau {network['name']} créé")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors de la création du réseau {network['name']}: {e}")
            raise

    def start_network(self, name: str):
        """Active un réseau."""
        try:
            print(f"  ✓ Tentative d'activation du réseau {name}...")
            net = self.conn.networkLookupByName(name)
            if net.isActive():
                print(f"  ! Réseau {name} est déjà actif")
                return
            print(f"  ✓ Démarrage du réseau {name}...")
            net.create()
            print(f"  ✓ Réseau {name} activé")
            # Vérifier à nouveau l'état du réseau
            if net.isActive():
                print(f"  ✓ Réseau {name} est maintenant actif")
            else:
                print(f"  ✗ Réseau {name} n'a pas pu être activé")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors de l'activation du réseau {name}: {e}")
            raise

    def deploy_networks(self):
        """Déploie tous les réseaux."""
        for network in self.infra.get('networks', []):
            print(f"Déploiement du réseau {network['name']}...")
            self.create_network(network)
            self.start_network(network['name'])

    def wait_for_cdrom(self, vm_name: str, timeout: int = 30, interval: int = 1) -> bool:
        """Attend que le périphérique CD-ROM soit prêt."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Vérifier si le périphérique CD-ROM est prêt
            check_cmd = "lsblk /dev/sr0"
            result = self.execute_via_qemu_agent(vm_name, check_cmd)
            result_decoded = decode_base64_fields(result)
            if result_decoded.get('success', False) and 'exitcode' in result_decoded.get('output', {}).get('return', {}) and result_decoded['output']['return']['exitcode'] == 0:
                print("  ✓ Périphérique CD-ROM prêt")
                return True
            time.sleep(interval)
        print("  ✗ Timeout atteint en attendant le périphérique CD-ROM")
        return False

    def apply_init_via_agent(self, vm: Dict):
        """Applique la configuration via qemu-guest-agent."""
        if 'cloud_init' in vm:
            print(f"  ✓ Configuration cloud_init trouvée pour {vm['name']}")
            # Appliquer la configuration cloud_init
            self.apply_cloud_init_via_agent(vm)
        elif 'clone_init' in vm:
            print(f"  ✓ Configuration clone_init trouvée pour {vm['name']}")
            # Appliquer la configuration clone_init
            self.apply_clone_init_via_agent(vm)
        else:
            print(f"  ✗ Aucune configuration d'initialisation trouvée pour {vm['name']}")
            return

    def apply_cloud_init_via_agent(self, vm: Dict):
        """Applique la configuration cloud_init via qemu-guest-agent."""
        if 'cloud_init' not in vm:
            print(f"  ✗ Aucune configuration cloud_init trouvée pour {vm['name']}")
            return False
        try:
            # Exemple de configuration cloud_init
            # Remplacer par la logique appropriée pour appliquer la configuration cloud_init
            print(f"  ✓ Application de la configuration cloud_init pour {vm['name']}")
            # Exemple : Exécuter des commandes pour appliquer la configuration cloud_init
            return True
        except Exception as e:
            print(f"  ✗ Erreur lors de l'application de la configuration cloud_init pour {vm['name']}: {e}")
            return False

    def apply_clone_init_via_agent(self, vm: Dict):
        """Applique la configuration clone_init via qemu-guest-agent."""
        if 'clone_init' not in vm:
            print(f"  ✗ Aucune configuration clone_init trouvée pour {vm['name']}")
            return False
        try:
            # Exemple de configuration clone_init
            # Remplacer par la logique appropriée pour appliquer la configuration clone_init
            print(f"  ✓ Application de la configuration clone_init pour {vm['name']}")
            # Exemple : Exécuter des commandes pour appliquer la configuration clone_init
            return True
        except Exception as e:
            print(f"  ✗ Erreur lors de l'application de la configuration clone_init pour {vm['name']}: {e}")
            return False

    def install_vm(self, vm: Dict) -> bool:
        """Installe une nouvelle VM avec virt-install."""
        try:
            # Créer les disques
            for disk in vm['cloud_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2", 'size': vm['disk_size']}]):
                self._create_disk(disk['path'], disk.get('size', vm['disk_size']))

            # Générer l'ISO cloud-init
            cloud_init_iso = self._create_init_iso(vm, 'cloud_init')

            # Commande virt-install
            cmd = [
                "virt-install",
                "--name", vm['name'],
                "--ram", str(vm['ram']),
                "--vcpus", str(vm['cpu']),
                "--cpu", "qemu64",
                "--disk", f"path={vm['cloud_init']['disks'][0]['path']},size={vm['disk_size']},bus=virtio",
                "--location", os.path.join(ISO_DIR, vm['cloud_init']['iso']),
                "--extra-args", "console=ttyS0,115200n8 autoinstall ds=nocloud-net",
                "--console", "pty,target_type=serial",
                "--noautoconsole",
                "--network", f"network={vm['networks'][0]['name']}"
            ]
            cmd.extend(["--disk", f"path={cloud_init_iso},device=cdrom"])
            subprocess.run(cmd, check=True)
            print(f"  ✓ VM {vm['name']} installée avec autoinstall")
            return True
        except Exception as e:
            print(f"  ✗ Erreur lors de l'installation de la VM {vm['name']}: {e}")
            return False

    def _update_vm_networks_libvirt(self, vm_name: str, networks: List[Dict]):
        """Met à jour les réseaux d'une VM en utilisant libvirt."""
        try:
            # Obtenir la configuration XML actuelle de la VM
            domain = self.conn.lookupByName(vm_name)
            xml = domain.XMLDesc(0)

            # Charger le XML dans un objet ElementTree pour le modifier
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml)

            # Supprimer toutes les interfaces réseau existantes
            for interface in root.findall('devices/interface'):
                root.find('devices').remove(interface)

            # Ajouter les nouvelles interfaces réseau
            devices = root.find('devices')
            for network in networks:
                interface = ET.SubElement(devices, 'interface', {'type': 'network'})
                ET.SubElement(interface, 'source', {'network': network['name']})
                ET.SubElement(interface, 'model', {'type': 'virtio'})

            # Convertir l'objet ElementTree en chaîne XML
            new_xml = ET.tostring(root, encoding='unicode')

            # Définir la nouvelle configuration XML
            self.conn.defineXML(new_xml)
            print(f"  ✓ Réseaux mis à jour pour {vm_name}")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors de la mise à jour des réseaux pour {vm_name}: {e}")
        except Exception as e:
            print(f"  ✗ Erreur lors de la mise à jour des réseaux pour {vm_name}: {e}")

    def _clone_vm(self, source_vm_name: str, target_vm: Dict) -> bool:
        """Clone une VM existante."""
        try:
            cmd = [
                "virt-clone",
                "--original", source_vm_name,
                "--name", target_vm['name'],
                "--auto-clone"
            ]
            subprocess.run(cmd, check=True)
            print(f"  ✓ VM {target_vm['name']} clonée à partir de {source_vm_name}")

            # Mettre à jour le réseau de la VM clonée
            if 'networks' in target_vm:
                self._update_vm_networks_libvirt(target_vm['name'], target_vm['networks'])

            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Erreur lors du clonage de la VM {target_vm['name']}: {e}")
            return False

    def clone_vm(self, source_vm_name: str, target_vm: Dict) -> bool:
        """Clone une VM existante."""
        try:
            # Cloner la VM
            if not self._clone_vm(source_vm_name, target_vm):
                return False

            # Créer l'ISO clone_init
            clone_init_iso = self._create_init_iso(target_vm, 'clone_init')

            # Attacher l'ISO à la VM clonée
            if not self._attach_iso_to_vm(target_vm['name'], clone_init_iso):
                return False

            # Démarrer la VM
            self.start_vm(target_vm['name'])

            # Agrandir le disque
            if not self._resize_disk(target_vm):
                return False

            return True
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors du clonage de la VM {target_vm['name']}: {e}")
            return False

    def _attach_iso_to_vm(self, vm_name: str, iso_path: str) -> bool:
        """Attache une ISO à une VM."""
        try:
            cmd = [
                "virsh",
                "attach-disk",
                vm_name,
                iso_path,
                "--type", "cdrom",
                "--target", "sdc",  # Utiliser un périphérique SATA différent
                "--persistent"
            ]
            subprocess.run(cmd, check=True)
            print(f"  ✓ ISO attachée à la VM {vm_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Erreur lors de l'attachement de l'ISO à la VM {vm_name}: {e}")
            return False

    def _resize_disk(self, vm: Dict) -> bool:
        """Agrandit le disque d'une VM."""
        try:
            for disk in vm['clone_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2", 'size': vm['disk_size']}]):
                disk_path = disk['path']
                new_size_gb = disk.get('size', vm['disk_size'])
                cmd = [
                    "virsh",
                    "blockresize",
                    vm['name'],
                    "--path", disk_path,
                    "--size", f"{new_size_gb}G"
                ]
                subprocess.run(cmd, check=True)
                print(f"  ✓ Disque {disk_path} agrandi à {new_size_gb}G")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Erreur lors de l'agrandissement du disque pour {vm['name']}: {e}")
            return False

    def wait_for_vm_shutdown(self, name: str, timeout: int = 3000, interval: int = 1) -> bool:
        """Attend qu'une VM s'éteigne."""
        start_time = time.time()
        print(f"\n⏳ Attente de l'extinction de la VM {name}...")
        while True:
            domain = self.conn.lookupByName(name)
            if not domain.isActive():
                print(f"✅ VM {name} est éteinte !")
                return True
            if time.time() - start_time > timeout:
                print(f"❌ Timeout atteint après {timeout} secondes pour la VM {name}.")
                return False
            time.sleep(interval)

    def start_vm(self, name: str):
        """Démarre une VM."""
        try:
            domain = self.conn.lookupByName(name)
            if domain.isActive():
                print(f"  ! VM {name} est déjà démarrée")
                return
            domain.create()
            print(f"  ✓ VM {name} démarrée")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors du démarrage de la VM {name}: {e}")
            raise

    def execute_via_qemu_agent(self, vm_name: str, command, username: str = "root", wait_for_completion: bool = True, timeout: int = 30) -> Dict:
        """
        Exécute une commande dans une VM via qemu-guest-agent avec l'utilisateur spécifié et retourne si elle s'est bien exécutée ou non.
        """
        try:
            # Liste des commandes internes qui ne doivent pas être modifiées
            internal_commands = ["guest-ping", "guest-sync", "guest-get-users", "guest-exec-status", "guest-info", "guest-get-fsinfo", "guest-get-disks", "guest-network-get-interfaces", "guest-file-open", "guest-file-write", "guest-file-close"]
            # Si la commande est une commande interne, ne pas la modifier
            if isinstance(command, dict) and command.get("execute") in internal_commands:
                command_dict = command
            elif isinstance(command, str) and command in internal_commands:
                command_dict = {"execute": command}
            else:
                # Si la commande est une chaîne de caractères, la traiter comme une commande normale
                if isinstance(command, str):
                    parts = command.split()
                    path = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    command_dict = {
                        "execute": "guest-exec",
                        "arguments": {
                            "path": path,
                            "arg": args,
                            "capture-output": True
                        }
                    }
                elif isinstance(command, dict):
                    # Si la commande est déjà un dictionnaire, l'utiliser directement
                    command_dict = command
                else:
                    raise ValueError("La commande doit être une chaîne de caractères ou un dictionnaire")
            # Exécution de la commande
            cmd = [
                "virsh",
                "qemu-agent-command",
                vm_name,
                json.dumps(command_dict)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                return {
                    'success': False,
                    'output': None,
                    'error': f"Erreur lors de l'exécution de la commande: {result.stderr}",
                    'pid': None
                }
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'output': None,
                    'error': f"Réponse invalide de l'agent: {result.stdout}",
                    'pid': None
                }
            # Vérifier si la commande est de type guest-exec et si nous devons attendre la fin de l'exécution
            if command_dict.get("execute") == "guest-exec" and 'return' in output and 'pid' in output['return'] and wait_for_completion:
                pid = output['return']['pid']
                # Attendre que la commande se termine
                while True:  # Attendre indéfiniment si timeout est désactivé
                    time.sleep(1)
                    status_cmd = {
                        "execute": "guest-exec-status",
                        "arguments": {
                            "pid": pid
                        }
                    }
                    status_result = subprocess.run([
                        "virsh",
                        "qemu-agent-command",
                        vm_name,
                        json.dumps(status_cmd)
                    ], capture_output=True, text=True, timeout=10)
                    if status_result.returncode != 0:
                        continue
                    try:
                        status_output = json.loads(status_result.stdout)
                        if 'return' in status_output and status_output['return'].get('exited', False):
                            return {
                                'success': True,
                                'output': status_output,
                                'error': None,
                                'pid': pid
                            }
                    except json.JSONDecodeError:
                        continue
            # Vérifier si la commande a été exécutée avec succès
            elif 'return' in output:
                return {
                    'success': True,
                    'output': output,
                    'error': None,
                    'pid': None
                }
            else:
                return {
                    'success': False,
                    'output': output,
                    'error': "La commande n'a pas retourné de résultat valide",
                    'pid': None
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': None,
                'error': "Timeout atteint après 30 secondes",
                'pid': None
            }
        except Exception as e:
            return {
                'success': False,
                'output': None,
                'error': str(e),
                'pid': None
            }

    def wait_for_agent(self, vm_name: str, timeout: int = 600) -> bool:
        """Attend que le qemu-guest-agent soit disponible."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            print("Waiting for agent...")
            # Essayer guest-ping
            test_cmd = "guest-ping"
            result = self.execute_via_qemu_agent(vm_name, test_cmd)
            if result['success'] and result['output'].get('return') == {}:
                print("Agent QEMU disponible !")
                return True
            if result['error'] and "not configured" in result['error']:
                print(f"Le canal QEMU Guest Agent n'est pas configuré pour {vm_name}")
                return False
            time.sleep(1)
        print(f"Timeout atteint pour l'agent QEMU de {vm_name}")
        return False

    def copy_files_via_agent(self, vm: Dict):
        """Copie des fichiers dans la VM via qemu-guest-agent."""
        if 'copy_files' not in vm:
            return
        for file_item in vm['copy_files']:
            source_path = os.path.join(FILES_DIR, file_item['source'])
            if not os.path.exists(source_path):
                print(f"  ✗ Source introuvable: {source_path}")
                continue
            dest_path = file_item['destination']
            if os.path.isdir(source_path):
                self._copy_directory_via_agent(vm['name'], source_path, dest_path)
            else:
                self._copy_file_via_agent(vm['name'], source_path, dest_path)

    def _create_directory_via_agent(self, vm_name: str, path: str) -> bool:
        """Crée un répertoire dans la VM via guest-exec."""
        path = os.path.normpath(path)
        if not path.startswith('/'):
            path = '/' + path
        cmd = f"/bin/mkdir -p {path}"
        result = self.execute_via_qemu_agent(vm_name, cmd)
        if result['success']:
            print(f"  ✓ Répertoire {path} créé dans {vm_name}")
            return True
        else:
            print(f"  ✗ Erreur lors de la création du répertoire {path}: {result['error']}")
            return False

    def _copy_file_via_agent(self, vm_name: str, source_path: str, dest_path: str) -> bool:
        """Copie un fichier dans la VM."""
        try:
            # Créer le répertoire parent si nécessaire
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and dest_dir != '/' and not self._create_directory_via_agent(vm_name, dest_dir):
                return False
            # Lire le contenu du fichier source
            with open(source_path, 'rb') as f:
                content = f.read()
            content_b64 = base64.b64encode(content).decode('utf-8')
            # Écrire le fichier
            file_handle = None
            try:
                # Ouvrir le fichier
                open_cmd = f"guest-file-open {dest_path} w"
                open_result = self.execute_via_qemu_agent(vm_name, open_cmd)
                if not open_result['success']:
                    raise RuntimeError(f"Erreur lors de l'ouverture du fichier: {open_result['error']}")
                file_handle = open_result['output']['return']
                # Écrire le contenu par blocs
                chunk_size = 4 * 1024 * 1024  # 4MB
                for i in range(0, len(content_b64), chunk_size):
                    chunk = content_b64[i:i+chunk_size]
                    write_cmd = f"guest-file-write {file_handle} {chunk}"
                    write_result = self.execute_via_qemu_agent(vm_name, write_cmd)
                    if not write_result['success']:
                        raise RuntimeError(f"Erreur lors de l'écriture: {write_result['error']}")
                print(f"  ✓ Fichier {source_path} copié vers {dest_path}")
                return True
            finally:
                if file_handle is not None:
                    close_cmd = f"guest-file-close {file_handle}"
                    self.execute_via_qemu_agent(vm_name, close_cmd)
        except Exception as e:
            print(f"  ✗ Erreur lors de la copie du fichier {source_path}: {e}")
            return False

    def _write_file_via_agent(self, vm_name: str, dest_path: str, content_b64: str) -> bool:
        """Écrit un fichier dans la VM via guest-file-open et guest-file-write."""
        # Créer le répertoire parent si nécessaire
        dest_dir = os.path.dirname(dest_path)
        if dest_dir and dest_dir != '/' and not self._create_directory_via_agent(vm_name, dest_dir):
            print(f"  ✗ Échec de la création du répertoire parent {dest_dir}")
            return False
        # Ouvrir le fichier
        open_cmd = {
            "execute": "guest-file-open",
            "arguments": {
                "path": dest_path,
                "mode": "w"
            }
        }
        open_result = self.execute_via_qemu_agent(vm_name, open_cmd)
        if not open_result['success']:
            print(f"  ✗ Échec de l'ouverture du fichier {dest_path}: {open_result['error']}")
            return False
        file_handle = open_result['output']['return']
        try:
            # Écrire le contenu par morceaux
            chunk_size = 4 * 1024 * 1024  # 4MB
            for i in range(0, len(content_b64), chunk_size):
                chunk = content_b64[i:i+chunk_size]
                write_cmd = {
                    "execute": "guest-file-write",
                    "arguments": {
                        "handle": file_handle,
                        "buf-b64": chunk
                    }
                }
                write_result = self.execute_via_qemu_agent(vm_name, write_cmd)
                if not write_result['success']:
                    print(f"  ✗ Échec de l'écriture du fichier {dest_path}: {write_result['error']}")
                    return False
            return True
        finally:
            close_cmd = {
                "execute": "guest-file-close",
                "arguments": {
                    "handle": file_handle
                }
            }
            close_result = self.execute_via_qemu_agent(vm_name, close_cmd)
            if not close_result['success']:
                print(f"  ✗ Échec de la fermeture du fichier {dest_path}: {close_result['error']}")

    def _copy_directory_via_agent(self, vm_name: str, source_dir: str, dest_dir: str) -> bool:
        """Copie un répertoire (avec sous-répertoires) dans la VM."""
        try:
            # Normaliser les chemins
            source_dir = os.path.normpath(source_dir)
            dest_dir = os.path.normpath(dest_dir)
            # Vérifier que le répertoire source existe
            if not os.path.exists(source_dir):
                print(f"  ✗ Répertoire source {source_dir} introuvable")
                return False
            # Créer une archive tar.gz
            tar_path = "/tmp/copy_dir.tar.gz"
            parent_dir = os.path.dirname(source_dir)
            dir_name = os.path.basename(source_dir)
            subprocess.run([
                "tar", "czf", tar_path,
                "-C", parent_dir,
                dir_name
            ], check=True)
            # Lire l'archive
            with open(tar_path, 'rb') as f:
                tar_content = f.read()
            tar_content_b64 = base64.b64encode(tar_content).decode('utf-8')
            # Créer le répertoire de destination
            if not self._create_directory_via_agent(vm_name, dest_dir):
                return False
            # Écrire l'archive dans la VM
            archive_dest = f"{dest_dir}/archive.tar.gz"
            if not self._write_file_via_agent(vm_name, archive_dest, tar_content_b64):
                return False
            # Extraire l'archive
            extract_cmd = f"/bin/tar xzf {archive_dest} -C {dest_dir}"
            extract_result = self.execute_via_qemu_agent(vm_name, extract_cmd)
            if not extract_result['success']:
                print(f"  ✗ Erreur lors de l'extraction de l'archive: {extract_result['error']}")
                return False
            # Supprimer l'archive
            rm_cmd = f"/bin/rm -f {archive_dest}"
            self.execute_via_qemu_agent(vm_name, rm_cmd)
            print(f"  ✓ Répertoire {source_dir} copié vers {dest_dir}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Erreur lors de la création de l'archive: {e}")
            return False
        except Exception as e:
            print(f"  ✗ Erreur lors de la copie du répertoire {source_dir}: {e}")
            return False
        finally:
            if 'tar_path' in locals() and os.path.exists(tar_path):
                try:
                    os.remove(tar_path)
                except:
                    pass

    def run_scripts_via_agent(self, vm: Dict):
        """Exécute les scripts dans la VM."""
        if 'post_install_scripts' not in vm:
            print(f"  ! Aucun script à exécuter pour {vm['name']}")
            return
        for script in vm['post_install_scripts']:
            script_path = os.path.join(SCRIPTS_DIR, script)
            if not os.path.exists(script_path):
                print(f"  ✗ Script introuvable: {script_path}")
                continue
            # Chemin de destination
            script_dest = f"/tmp/{os.path.basename(script_path)}"
            print(f"  - Copie du script {script_path} vers {script_dest}")
            # Lire le contenu du script
            with open(script_path, 'rb') as f:
                script_content = f.read()
            script_content_b64 = base64.b64encode(script_content).decode('utf-8')
            # Écrire le script dans la VM
            if not self._write_file_via_agent(vm['name'], script_dest, script_content_b64):
                print(f"  ✗ Échec de l'écriture du script {script} dans {vm['name']}")
                continue
            # Donner les permissions d'exécution
            chmod_cmd = {
                "execute": "guest-exec",
                "arguments": {
                    "path": "/bin/chmod",
                    "arg": ["+x", script_dest],
                    "capture-output": True
                }
            }
            chmod_result = self.execute_via_qemu_agent(vm['name'], chmod_cmd)
            if not chmod_result['success']:
                print(f"  ✗ Échec de la modification des permissions pour {script_dest}: {chmod_result['error']}")
                continue
            # Exécuter le script
            exec_cmd = {
                "execute": "guest-exec",
                "arguments": {
                    "path": script_dest,
                    "capture-output": True
                }
            }
            exec_result = self.execute_via_qemu_agent(vm['name'], exec_cmd)
            if exec_result['success']:
                print(f"  ✓ Script {script} exécuté sur {vm['name']}")
            else:
                print(f"  ✗ Erreur lors de l'exécution du script {script}: {exec_result['error']}")

    def deploy_vms(self):
        """Déploie toutes les VMs."""
        # Étape 1: Boucle pour les installations et clônages
        for vm in self.infra['vms']:
            if not self.vm_exists(vm['name']):
                if 'cloud_init' in vm:
                    if not self.install_vm(vm):
                        print(f"  ✗ Échec de l'installation de la VM {vm['name']}")
                        continue
                elif 'clone_init' in vm:
                    source_vm_name = vm['clone_init']['source_vm']
                    if not self.clone_vm(source_vm_name, vm):
                        print(f"  ✗ Échec du clonage de la VM {vm['name']}")
                        continue
                else:
                    print(f"  ✗ Configuration manquante pour la VM {vm['name']}: ni cloud_init ni clone_init spécifié")
                    continue

        # Étape 2: Boucle pour le reste en multithreading
        conn_lock = threading.Lock()
        threads = []
        for vm in self.infra['vms']:
            thread = threading.Thread(target=self.deploy_vm, args=(vm, conn_lock))
            threads.append(thread)
            thread.start()

        # Attendre que tous les threads soient terminés
        for thread in threads:
            thread.join()

    def run_configure_vm_script(self, vm_name: str) -> bool:
        """Exécute le script configure_vm sur une VM."""
        configure_vm_script = os.path.join(SCRIPTS_DIR, "clone/configure_vm.py")
        if not os.path.exists(configure_vm_script):
            print(f"  ✗ Script configure_vm introuvable: {configure_vm_script}")
            return False

        print(f"  - Exécution du script configure_vm sur {vm_name}")
        script_dest = f"/tmp/configure_vm.py"

        try:
            # Lire le contenu du script
            with open(configure_vm_script, 'rb') as f:
                script_content = f.read()
            script_content_b64 = base64.b64encode(script_content).decode('utf-8')

            # Écrire le script dans la VM
            if not self._write_file_via_agent(vm_name, script_dest, script_content_b64):
                print(f"  ✗ Échec de l'écriture du script configure_vm dans {vm_name}")
                return False

            # Donner les permissions d'exécution
            chmod_cmd = {
                "execute": "guest-exec",
                "arguments": {
                    "path": "/bin/chmod",
                    "arg": ["+x", script_dest],
                    "capture-output": True
                }
            }
            chmod_result = self.execute_via_qemu_agent(vm_name, chmod_cmd)
            if not chmod_result['success']:
                print(f"  ✗ Échec de la modification des permissions pour {script_dest}: {chmod_result['error']}")
                return False

            # Créer le répertoire de montage pour l'ISO
            mount_dir = "/mnt"
            mkdir_cmd = f"/bin/mkdir -p {mount_dir}"
            mkdir_result = self.execute_via_qemu_agent(vm_name, mkdir_cmd)
            if not mkdir_result['success']:
                print(f"  ✗ Échec de la création du répertoire de montage {mount_dir}: {mkdir_result['error']}")
                return False

            # Monter l'ISO
            mount_cmd = f"/bin/mount /dev/sr0 {mount_dir}"
            mount_result = self.execute_via_qemu_agent(vm_name, mount_cmd)
            if not mount_result['success']:
                print(f"  ✗ Échec du montage de l'ISO: {mount_result['error']}")
                return False

            # Exécuter le script
            exec_cmd = {
                "execute": "guest-exec",
                "arguments": {
                    "path": script_dest,
                    "capture-output": True
                }
            }
            exec_result = self.execute_via_qemu_agent(vm_name, exec_cmd)
            if exec_result['success']:
                print(f"  ✓ Script configure_vm exécuté sur {vm_name}")
                return True
            else:
                print(f"  ✗ Erreur lors de l'exécution du script configure_vm: {exec_result['error']}")
                return False
        except Exception as e:
            print(f"  ✗ Erreur lors de l'exécution du script configure_vm: {e}")
            return False

    def deploy_vm(self, vm, conn_lock):
        """Déploie une seule VM."""
        try:
            with conn_lock:
                self.conn = libvirt.open("qemu:///system")
            print(f"\nDéploiement de la VM {vm['name']}...")

            # Vérifier si la VM existe déjà
            if self.vm_exists(vm['name']):
                print(f"  ! VM {vm['name']} existe déjà, ignorée")
            else:
                # Étape 3: Configurer la VM existante
                template = env.get_template('vm.xml.j2')
                vm_xml = template.render(vm=vm, vm_images_dir=VM_IMAGES_DIR)
                try:
                    self.conn.defineXML(vm_xml)
                    print(f"  ✓ VM {vm['name']} configurée")
                except libvirt.libvirtError as e:
                    print(f"  ✗ Erreur lors de la configuration de la VM {vm['name']}: {e}")
                    return

            # Étape 4: Attendre que la VM s'éteigne après l'installation (si nécessaire)
            if 'cloud_init' in vm:
                if not self.wait_for_vm_shutdown(vm['name']):
                    print(f"  ✗ Échec de l'attente de l'extinction de la VM {vm['name']}")
                    return

            # Étape 5: Démarrer la VM
            self.start_vm(vm['name'])

            # Étape 6: Attendre que l'agent QEMU soit disponible et appliquer la configuration clone_init si nécessaire
            if 'clone_init' in vm:
                if not self.wait_for_agent(vm['name']):
                    print(f"  ❌ Timeout atteint en attendant qemu-guest-agent pour {vm['name']}")
                    return
                if not self.apply_clone_init_via_agent(vm):
                    print(f"  ✗ Échec de l'application de la configuration clone_init pour {vm['name']}")
                    return

                # Exécuter le script configure_vm pour les VMs clonées
                if not self.run_configure_vm_script(vm['name']):
                    print(f"  ✗ Échec de l'exécution du script configure_vm sur {vm['name']}")

            # Étape 7: Copier les fichiers dans la VM
            self.copy_files_via_agent(vm)

            # Étape 8: Exécuter les scripts post-installation
            self.run_scripts_via_agent(vm)

        except Exception as e:
            print(f"  ✗ Erreur lors du déploiement de la VM {vm['name']}: {e}")

    def _create_init_iso(self, vm: Dict, init_type: str) -> str:
        """Génère une ISO d'initialisation."""
        if init_type == 'cloud_init':
            meta_data = "\n".join(f"{k}: {v}" for k, v in vm['cloud_init'].get('meta_data', {}).items())
            user_data_str = "#cloud-config\n" + yaml.dump(vm['cloud_init']['user_data'], default_flow_style=False, sort_keys=False)
        elif init_type == 'clone_init':
            meta_data = "\n".join(f"{k}: {v}" for k, v in vm['clone_init'].get('meta_data', {}).items())
            user_data_str = "#cloud-config\n" + yaml.dump(vm['clone_init']['user_data'], default_flow_style=False, sort_keys=False)
        else:
            print(f"  ✗ Type d'initialisation inconnu: {init_type}")
            return None
        with open("/tmp/meta-data", "w") as f:
            f.write(meta_data)
        with open("/tmp/user-data", "w") as f:
            f.write(user_data_str)
        iso_path = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-{init_type}.iso")
        subprocess.run([
            'genisoimage', '-input-charset', 'utf-8',
            '-output', iso_path,
            '-volid', 'cidata', '-joliet', '-rock',
            '/tmp/meta-data', '/tmp/user-data'
        ], check=True)
        print(f"  ✓ ISO {init_type} générée: {iso_path}")
        return iso_path

    def _create_disk(self, path: str, size_gb: int):
        """Crée un disque qcow2."""
        if os.path.exists(path):
            print(f"  ! Disque {path} existe déjà, ignoré")
            return
        subprocess.run(['qemu-img', 'create', '-f', 'qcow2', path, f"{size_gb}G"], check=True)
        print(f"  ✓ Disque {path} créé ({size_gb} Go)")

    def deploy_firewall(self):
        """Affiche les règles de pare-feu."""
        if 'firewall' not in self.infra:
            return
        print("\nRègles de pare-feu à appliquer manuellement:")
        for rule in self.infra['firewall']['rules']:
            action = "AUTHORISER" if rule['action'] == "allow" else "REFUSER"
            print(f"  {action} {rule['protocol']}/{rule['port']} vers {rule['vm']} depuis {rule['source']}")

    def clean(self):
        """Nettoie l'infrastructure."""
        print(f"Nettoyage de l'infrastructure {self.infra['name']}...")
        for vm in self.infra['vms']:
            self._clean_vm(vm)
        for network in reversed(self.infra.get('networks', [])):
            self._clean_network(network)
        print("\n✅ Nettoyage terminé !")

    def _clean_vm(self, vm: Dict):
        """Supprime une VM et ses ressources."""
        print(f"Suppression de la VM {vm['name']}...")
        if not self.vm_exists(vm['name']):
            print(f"  ! VM {vm['name']} non trouvée")
            return
        domain = self.conn.lookupByName(vm['name'])
        if domain.isActive():
            domain.destroy()
            print(f"  ✓ VM {vm['name']} arrêtée")
        domain.undefine()
        print(f"  ✓ VM {vm['name']} supprimée")
        if 'cloud_init' in vm:
            for disk in vm['cloud_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2"}]):
                if os.path.exists(disk['path']):
                    os.remove(disk['path'])
                    print(f"  ✓ Disque {disk['path']} supprimé")
            cloud_init_iso = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloudinit.iso")
            print(f"  Chemin de l'ISO cloud-init: {cloud_init_iso}")
            if os.path.exists(cloud_init_iso):
                os.remove(cloud_init_iso)
                print(f"  ✓ ISO cloud-init {cloud_init_iso} supprimée")
            else:
                print(f"  ! ISO cloud-init {cloud_init_iso} non trouvée")
        elif 'clone_init' in vm:
            for disk in vm['clone_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2"}]):
                if 'source_vm' in vm['clone_init'] and vm['clone_init']['source_vm'] in disk['path']:
                    print(f"  ! Disque source {disk['path']} non supprimé")
                    continue
                if os.path.exists(disk['path']):
                    os.remove(disk['path'])
                    print(f"  ✓ Disque {disk['path']} supprimé")
            clone_init_iso = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloneinit.iso")
            print(f"  Chemin de l'ISO clone_init: {clone_init_iso}")
            if os.path.exists(clone_init_iso):
                os.remove(clone_init_iso)
                print(f"  ✓ ISO clone_init {clone_init_iso} supprimée")
            else:
                print(f"  ! ISO clone_init {clone_init_iso} non trouvée")

    def _clean_network(self, network: Dict):
        """Supprime un réseau."""
        print(f"Suppression du réseau {network['name']}...")
        if not any(net.name() == network['name'] for net in self.conn.listAllNetworks()):
            print(f"  ! Réseau {network['name']} non trouvé")
            return
        net = self.conn.networkLookupByName(network['name'])
        if net.isActive():
            net.destroy()
            print(f"  ✓ Réseau {network['name']} désactivé")
        net.undefine()
        print(f"  ✓ Réseau {network['name']} supprimé")

    def deploy(self):
        """Déploie l'infrastructure complète."""
        print(f"Déploiement de l'infrastructure {self.infra['name']}...")
        self.deploy_networks()
        self.deploy_vms()
        self.deploy_firewall()
        print("\n✅ Déploiement terminé !")

# Fonctions utilitaires
def netmask(cidr: str) -> str:
    import ipaddress
    network = ipaddress.IPv4Network(cidr, strict=False)
    return str(network.netmask)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Déployer/nettoyer une infrastructure KVM/QEMU.")
    parser.add_argument("yaml_file", help="Chemin vers le fichier YAML")
    parser.add_argument("--clean", action="store_true", help="Nettoyer l'infrastructure")
    args = parser.parse_args()
    try:
        deployer = InfraDeployer(args.yaml_file)
        deployer.check_prerequisites()
        deployer.load_infra()
        if args.clean:
            deployer.clean()
        else:
            deployer.deploy()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        exit(1)
