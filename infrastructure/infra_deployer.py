#!/usr/bin/env python3
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
from pathlib import Path
from typing import Dict, List, Optional

# Chemins et constants
ISO_DIR = "/var/lib/libvirt/isos"
VM_IMAGES_DIR = "/var/lib/libvirt/images"
CLOUD_INIT_ISO_DIR = "/var/lib/libvirt/cloud_init_isos"
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
SHARED_DIR = "/var/lib/libvirt/shared"
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")

# Initialiser Jinja2 pour les templates
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True
)

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
        if not os.path.exists(SHARED_DIR):
            errors.append(f"Le répertoire {SHARED_DIR} n'existe pas")
        else:
            mode = os.stat(SHARED_DIR).st_mode
            if not (mode & 0o777) == 0o777:
                errors.append(f"Le répertoire {SHARED_DIR} n'a pas les permissions 777")
        if errors:
            raise RuntimeError("Prérequis non satisfaits:\n" + "\n".join(f"  - {e}" for e in errors))

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
        if self.network_is_active(name):
            print(f"  ! Réseau {name} est déjà actif")
            return
        try:
            net = self.conn.networkLookupByName(name)
            net.create()
            print(f"  ✓ Réseau {name} activé")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors de l'activation du réseau {name}: {e}")
            raise

    def deploy_networks(self):
        """Déploie tous les réseaux."""
        for network in self.infra.get('networks', []):
            print(f"Déploiement du réseau {network['name']}...")
            self.create_network(network)
            self.start_network(network['name'])

    def install_vm(self, vm: Dict):
        """Installe une nouvelle VM avec virt-install."""
        if self.vm_exists(vm['name']):
            print(f"  ! VM {vm['name']} existe déjà, ignorée")
            return
        # Créer les disques
        for disk in vm['cloud_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2", 'size': vm['disk_size']}]):
            self._create_disk(disk['path'], disk.get('size', vm['disk_size']))
        # Générer l'ISO cloud-init
        cloud_init_iso = self._create_cloud_init_iso(vm)
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

    def clone_vm(self, source_vm_name: str, target_vm: Dict):
        """Clone une VM existante."""
        if self.vm_exists(target_vm['name']):
            print(f"  ! VM {target_vm['name']} existe déjà, ignorée")
            return
        try:
            source_domain = self.conn.lookupByName(source_vm_name)
        except libvirt.libvirtError:
            print(f"  ✗ VM source {source_vm_name} non trouvée dans libvirt")
            return
        # Créer le disque pour la VM clonée
        for disk in target_vm['clone_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{target_vm['name']}.qcow2", 'size': target_vm['disk_size']}]):
            source_disk_path = f"{VM_IMAGES_DIR}/{source_vm_name}.qcow2"
            if not os.path.exists(source_disk_path):
                print(f"  ✗ Disque source {source_disk_path} introuvable")
                return
            source_disk_size = self._get_disk_size(source_disk_path)
            target_disk_size = disk.get('size', target_vm['disk_size'])
            self._create_disk(disk['path'], target_disk_size)
            subprocess.run(['qemu-img', 'create', '-f', 'qcow2', '-b', source_disk_path, '-F', 'qcow2', disk['path']], check=True)
            if target_disk_size > source_disk_size:
                self._resize_disk(disk['path'], target_disk_size)
        # Créer le XML pour la VM clonée
        template = env.get_template('vm.xml.j2')
        vm_xml = template.render(vm=target_vm, vm_images_dir=VM_IMAGES_DIR)
        try:
            self.conn.defineXML(vm_xml)
            print(f"  ✓ VM {target_vm['name']} clonée à partir de {source_vm_name}")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors du clonage de la VM {target_vm['name']}: {e}")
            raise

    def create_vm(self, vm: Dict):
        """Crée ou configure une VM."""
        if not self.vm_exists(vm['name']):
            if 'cloud_init' in vm:
                self.install_vm(vm)
            elif 'clone_init' in vm:
                source_vm_name = vm['clone_init']['source_vm']
                self.clone_vm(source_vm_name, vm)
        else:
            template = env.get_template('vm.xml.j2')
            vm_xml = template.render(vm=vm, vm_images_dir=VM_IMAGES_DIR)
            try:
                self.conn.defineXML(vm_xml)
                print(f"  ✓ VM {vm['name']} configurée")
            except libvirt.libvirtError as e:
                print(f"  ✗ Erreur lors de la configuration de la VM {vm['name']}: {e}")
                raise

    def wait_for_vm_shutdown(self, name: str, timeout: int = 300, interval: int = 1):
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

    def execute_via_qemu_agent(self, vm_name: str, command: Dict, timeout: int = 30) -> str:
        """Exécute une commande dans une VM via qemu-guest-agent."""
        try:
            cmd = [
                "virsh",
                "qemu-agent-command",
                vm_name,
                json.dumps(command)
            ]
            print(f"Exécutant la commande: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                print(f"Erreur lors de l'exécution de la commande: {result.stderr}")
                raise RuntimeError(f"Erreur lors de l'exécution de la commande dans {vm_name}: {result.stderr}")
            print(f"Résultat brut: {result.stdout}")
            return result.stdout
        except subprocess.TimeoutExpired:
            print(f"Timeout lors de l'exécution de la commande dans {vm_name}")
            raise
        except subprocess.CalledProcessError as e:
            print(f"Erreur appelée: {e.stderr}")
            raise RuntimeError(f"Erreur lors de l'exécution de la commande dans {vm_name}: {e.stderr}")
        except Exception as e:
            print(f"Autre erreur: {str(e)}")
            raise RuntimeError(f"Erreur lors de l'exécution de la commande dans {vm_name}: {str(e)}")


    def wait_for_agent(self, vm_name: str, timeout: int = 60) -> bool:
        """Attend que le qemu-guest-agent soit disponible."""
        start_time = time.time()
        print(f"Attente de l'agent QEMU pour {vm_name} (timeout: {timeout}s)...")

        while time.time() - start_time < timeout:
            try:
                test_cmd = {"execute": "guest-ping"}
                print(f"Tentative de ping de l'agent...")
                result = self.execute_via_qemu_agent(vm_name, test_cmd)
                print(f"Réponse brute: {result}")

                try:
                    output = json.loads(result)
                    print(f"Réponse JSON: {output}")
                    if 'return' in output and output.get('return') == {}:
                        print("Agent QEMU disponible !")
                        return True
                except json.JSONDecodeError as e:
                    print(f"Erreur de décodage JSON: {e}")
                    print(f"Réponse non-JSON: {result}")

                time.sleep(1)
            except Exception as e:
                print(f"Erreur lors de la tentative de ping: {str(e)}")
                time.sleep(1)

        print(f"Timeout atteint pour l'agent QEMU de {vm_name}")
        return False


    def copy_files_via_agent(self, vm: Dict):
        """Copie des fichiers/répertoires dans la VM."""
        if 'copy_files' not in vm:
            return

        for file_item in vm['copy_files']:
            source_path = os.path.join(FILES_DIR, file_item['source'])
            if not os.path.exists(source_path):
                print(f"  ✗ Source introuvable: {source_path}")
                continue

            # Vérifier que le chemin est absolu
            if not os.path.isabs(source_path):
                print(f"  ! Attention: {source_path} n'est pas un chemin absolu")
                continue

            if os.path.isdir(source_path):
                self._copy_directory_via_agent(vm['name'], source_path, file_item['destination'])
            else:
                self._copy_file_via_agent(vm['name'], source_path, file_item['destination'])

    def _copy_file_via_agent(self, vm_name: str, source_path: str, dest_path: str):
        """Copie un fichier unique dans la VM."""
        try:
            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                mkdir_cmd = {
                    "execute": "guest-exec",
                    "arguments": {
                        "path": "/bin/mkdir",
                        "arg": ["-p", dest_dir],
                        "capture-output": True
                    }
                }
                self.execute_via_qemu_agent(vm_name, mkdir_cmd)

            with open(source_path, 'rb') as f:
                content = f.read()

            content_b64 = base64.b64encode(content).decode('utf-8')
            cmd = {
                "execute": "guest-exec",
                "arguments": {
                    "path": "/bin/bash",
                    "arg": [f"echo '{content_b64}' | base64 -d > '{dest_path}'"],
                    "capture-output": True
                }
            }
            self.execute_via_qemu_agent(vm_name, cmd)
            print(f"  ✓ Fichier {source_path} copié vers {dest_path}")
        except Exception as e:
            print(f"  ✗ Erreur lors de la copie du fichier {source_path}: {e}")

    def _copy_directory_via_agent(self, vm_name: str, source_dir: str, dest_dir: str):
        """Copie un répertoire (avec sous-répertoires) dans la VM."""
        try:
            # Normaliser les chemins
            source_dir = os.path.normpath(source_dir)
            dir_name = os.path.basename(source_dir)

            # Vérifier que le répertoire existe et n'est pas vide
            if not os.path.exists(source_dir):
                print(f"  ✗ Répertoire source {source_dir} introuvable")
                return

            if not os.listdir(source_dir):
                print(f"  ! Répertoire {source_dir} est vide, ignoré")
                return

            # Créer une archive tar.gz
            tar_path = "/tmp/copy_dir.tar.gz"
            parent_dir = os.path.dirname(source_dir)

            subprocess.run([
                "tar", "czf", tar_path,
                "-C", parent_dir,
                dir_name
            ], check=True)

            # Lire et envoyer l'archive
            with open(tar_path, 'rb') as f:
                tar_content = f.read()

            tar_content_b64 = base64.b64encode(tar_content).decode('utf-8')

            # Commande pour la VM
            cmd = {
                "execute": "guest-exec",
                "arguments": {
                    "path": "/bin/bash",
                    "arg": [
                        f"echo '{tar_content_b64}' | base64 -d > /tmp/copy_dir.tar.gz && "
                        f"mkdir -p '{os.path.dirname(dest_dir)}' && "
                        f"tar xzf /tmp/copy_dir.tar.gz -C '{os.path.dirname(dest_dir)}' && "
                        "rm /tmp/copy_dir.tar.gz"
                    ],
                    "capture-output": True
                }
            }

            self.execute_via_qemu_agent(vm_name, cmd)
            print(f"  ✓ Répertoire {source_dir} copié vers {dest_dir}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Erreur lors de la création de l'archive: {e}")
            print(f"  ! Commande tar échouée pour {source_dir}")
        except Exception as e:
            print(f"  ✗ Erreur lors de la copie du répertoire {source_dir}: {e}")
        finally:
            # Nettoyer l'archive temporaire
            if os.path.exists(tar_path):
                try:
                    os.remove(tar_path)
                except:
                    pass

    def apply_clone_init_via_agent(self, vm: Dict):
        """Applique la configuration clone_init."""
        clone_init_iso = self._create_clone_init_iso(vm)
        with open(clone_init_iso, 'rb') as f:
            iso_content = f.read()

        iso_content_b64 = base64.b64encode(iso_content).decode('utf-8')
        cmd = {
            "execute": "guest-exec",
            "arguments": {
                "path": "/bin/bash",
                "arg": [
                    f"echo '{iso_content_b64}' | base64 -d > /tmp/clone-init.iso && "
                    "mkdir -p /mnt && "
                    "mount -o loop /tmp/clone-init.iso /mnt && "
                    "cp -r /mnt/* /opt/ && "
                    "umount /mnt && "
                    "rm /tmp/clone-init.iso"
                ],
                "capture-output": True
            }
        }
        try:
            self.execute_via_qemu_agent(vm['name'], cmd)
            print(f"  ✓ Configuration clone_init appliquée à {vm['name']}")
        except Exception as e:
            print(f"  ✗ Erreur lors de l'application de la configuration clone_init: {e}")

    def run_scripts_via_agent(self, vm: Dict):
        """Copie et exécute tous les scripts dans la VM."""
        scripts = vm.get('post_install_scripts', [])

        # Ajouter le script de configuration s'il existe
        config_script = os.path.join(SCRIPTS_DIR, "configure_vm.sh")
        if os.path.exists(config_script):
            scripts.append("configure_vm.sh")

        if not scripts:
            print(f"  ! Aucun script à exécuter pour {vm['name']}")
            return

        for script in scripts:
            script_path = os.path.join(SCRIPTS_DIR, script)
            if not os.path.exists(script_path):
                print(f"  ✗ Script introuvable: {script_path}")
                continue

            # 1. Copier le script dans la VM
            script_dest = f"/tmp/{os.path.basename(script_path)}"
            self._copy_file_via_agent(vm['name'], script_path, script_dest)

            # 2. Exécuter le script dans la VM
            cmd = {
                "execute": "guest-exec",
                "arguments": {
                    "path": "/bin/bash",
                    "arg": [
                        f"chmod +x {script_dest} && "
                        f"{script_dest}"
                    ],
                    "capture-output": True
                }
            }
            try:
                self.execute_via_qemu_agent(vm['name'], cmd)
                print(f"  ✓ Script {script} exécuté sur {vm['name']}")
            except Exception as e:
                print(f"  ✗ Erreur lors de l'exécution du script {script}: {e}")

    def deploy_vms_via_agent(self):
        """Déploie les VMs en utilisant exclusivement qemu-guest-agent."""
        for vm in self.infra['vms']:
            print(f"Déploiement de la VM {vm['name']}...")

            # Créer la VM
            self.create_vm(vm)

            # Attendre que la VM s'éteigne après l'installation
            if 'cloud_init' in vm:
                self.wait_for_vm_shutdown(vm['name'])

            # Démarrer la VM
            self.start_vm(vm['name'])
            # Attendre que l'agent soit disponible
            if not self.wait_for_agent(vm['name']):
                print(f"  ❌ Timeout atteint en attendant qemu-guest-agent pour {vm['name']}")
                continue

            # Configurer la VM
            if 'clone_init' in vm:
                self.apply_clone_init_via_agent(vm)

            # Copier les fichiers via l'agent
            self.copy_files_via_agent(vm)

            # Exécuter tous les scripts via l'agent
            self.run_scripts_via_agent(vm)

    def _get_disk_size(self, disk_path: str) -> int:
        """Obtient la taille d'un disque en Go."""
        result = subprocess.run(['qemu-img', 'info', '--output', 'json', disk_path], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Erreur lors de la récupération de la taille du disque {disk_path}: {result.stderr}")
        info = json.loads(result.stdout)
        return int(int(info['virtual-size']) / (1024 ** 3))

    def _resize_disk(self, disk_path: str, new_size_gb: int):
        """Agrandit un disque qcow2."""
        print(f"  ✓ Agrandissement du disque {disk_path} à {new_size_gb} Go")
        subprocess.run(['qemu-img', 'resize', disk_path, f"{new_size_gb}G"], check=True)

    def _create_cloud_init_iso(self, vm: Dict) -> str:
        """Génère une ISO cloud-init."""
        iso_path = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloudinit.iso")
        meta_data = "\n".join(f"{k}: {v}" for k, v in vm['cloud_init'].get('meta_data', {}).items())
        with open("/tmp/meta-data", "w") as f:
            f.write(meta_data)
        user_data_str = "#cloud-config\n" + yaml.dump(vm['cloud_init']['user_data'], default_flow_style=False, sort_keys=False)
        with open("/tmp/user-data", "w") as f:
            f.write(user_data_str)
        subprocess.run([
            'genisoimage', '-input-charset', 'utf-8',
            '-output', iso_path,
            '-volid', 'cidata', '-joliet', '-rock',
            '/tmp/meta-data', '/tmp/user-data'
        ], check=True)
        print(f"  ✓ ISO cloud-init générée: {iso_path}")
        return iso_path

    def _create_clone_init_iso(self, vm: Dict) -> str:
        """Génère une ISO clone_init."""
        iso_path = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloneinit.iso")
        meta_data = "\n".join(f"{k}: {v}" for k, v in vm['clone_init'].get('meta_data', {}).items())
        with open("/tmp/meta-data", "w") as f:
            f.write(meta_data)
        user_data_str = "#cloud-config\n" + yaml.dump(vm['clone_init']['user_data'], default_flow_style=False, sort_keys=False)
        with open("/tmp/user-data", "w") as f:
            f.write(user_data_str)
        subprocess.run([
            'genisoimage', '-input-charset', 'utf-8',
            '-output', iso_path,
            '-volid', 'cidata', '-joliet', '-rock',
            '/tmp/meta-data', '/tmp/user-data'
        ], check=True)
        print(f"  ✓ ISO clone_init générée: {iso_path}")
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
            if os.path.exists(cloud_init_iso):
                os.remove(cloud_init_iso)
                print(f"  ✓ ISO cloud-init {cloud_init_iso} supprimée")
        elif 'clone_init' in vm:
            for disk in vm['clone_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2"}]):
                if 'source_vm' in vm['clone_init'] and vm['clone_init']['source_vm'] in disk['path']:
                    print(f"  ! Disque source {disk['path']} non supprimé")
                    continue
                if os.path.exists(disk['path']):
                    os.remove(disk['path'])
                    print(f"  ✓ Disque {disk['path']} supprimé")
            clone_init_iso = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloneinit.iso")
            if os.path.exists(clone_init_iso):
                os.remove(clone_init_iso)
                print(f"  ✓ ISO clone_init {clone_init_iso} supprimée")

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
        self.deploy_vms_via_agent()
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
