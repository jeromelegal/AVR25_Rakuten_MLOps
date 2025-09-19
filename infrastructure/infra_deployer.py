#!/usr/bin/env python3
import os
import yaml
import libvirt
import jinja2
import subprocess
import grp
import pwd
from pathlib import Path
from typing import Dict, List, Optional

# Chemins et constants
ISO_DIR = "/var/lib/libvirt/isos"
VM_IMAGES_DIR = "/var/lib/libvirt/images"
CLOUD_INIT_ISO_DIR = "/var/lib/libvirt/cloud_init_isos"
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

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
        for dir_path in [ISO_DIR, VM_IMAGES_DIR, CLOUD_INIT_ISO_DIR]:
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
        if errors:
            raise RuntimeError("Prérequis non satisfaits:\n" + "\n".join(f"  - {e}" for e in errors))

    def load_infra(self):
        """Charge et valide le fichier YAML."""
        with open(self.yaml_file, 'r') as f:
            self.infra = yaml.safe_load(f)
        self._apply_defaults()
        self.validate()

    def _apply_defaults(self):
        """Applique les valeurs par défaut et hache les mots de passe."""
        for vm in self.infra['vms']:
            # Appliquer les defaults pour cloud_init
            if 'cloud_init' not in vm:
                vm['cloud_init'] = {}

            # Hacher le mot de passe s'il est en clair
            if 'cloud_init' in vm and 'user_data' in vm['cloud_init'] and 'autoinstall' in vm['cloud_init']['user_data']:
                identity = vm['cloud_init']['user_data']['autoinstall'].get('identity', {})
                if 'password' in identity:
                    plain_password = identity.pop('password')
                    identity['password'] = password_hash(plain_password)

    def validate(self):
        """Valide le fichier YAML."""
        errors = []
        # Vérifier que les ISO existent
        for vm in self.infra['vms']:
            if 'cloud_init' in vm and 'iso' in vm['cloud_init']:
                iso_path = os.path.join(ISO_DIR, vm['cloud_init']['iso'])
                if not os.path.exists(iso_path):
                    errors.append(f"ISO introuvable: {iso_path}")
        # Vérifier que les réseaux référencés existent
        network_names = {net['name'] for net in self.infra['networks']}
        for vm in self.infra['vms']:
            for net in vm.get('networks', []):
                if net['name'] not in network_names:
                    errors.append(f"Réseau {net['name']} non défini (utilisé par {vm['name']})")
        if errors:
            raise ValueError("Erreurs de validation:\n" + "\n".join(f"  - {e}" for e in errors))

    def network_exists(self, name: str) -> bool:
        """Vérifie si un réseau existe (actif ou inactif)."""
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
        domains = self.conn.listAllDomains(0)  # 0 = liste toutes les VMs (actives et inactives)
        for domain in domains:
            if domain.name() == name:
                return True
        return False

    def create_network(self, network: Dict):
        """Crée un réseau (sans l'activer)."""
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
        """Déploie tous les réseaux (création + activation)."""
        for network in self.infra['networks']:
            print(f"Déploiement du réseau {network['name']}...")
            self.create_network(network)
            self.start_network(network['name'])

    def install_vm(self, vm: Dict):
        """Installe une nouvelle VM avec virt-install et cloud-init."""
        if self.vm_exists(vm['name']):
            print(f"  ! VM {vm['name']} existe déjà, ignorée")
            return

        # Créer les disques
        for disk in vm['cloud_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2", 'size': vm.get('disk_size', 10)}]):
            self._create_disk(disk['path'], disk.get('size', vm.get('disk_size', 10)))

        # Générer l'ISO cloud-init
        cloud_init_iso = self._create_cloud_init_iso(vm)

        # Commande virt-install
        cmd = [
            "virt-install",
            "--name", vm['name'],
            "--ram", str(vm.get('ram', 3072)),
            "--vcpus", str(vm.get('cpu', 2)),
            "--cpu", "qemu64",
            "--disk", f"path={vm['cloud_init']['disks'][0]['path']},size={vm.get('disk_size', 10)},bus=virtio",
            "--location", os.path.join(ISO_DIR, vm['cloud_init']['iso']),
            "--extra-args", "console=ttyS0 autoinstall ds=nocloud-net",
            "--console", "pty,target_type=serial",
            "--noautoconsole"
        ]

        # Ajouter l'ISO cloud-init
        cmd.extend(["--disk", f"path={cloud_init_iso},device=cdrom"])

        # Exécuter la commande
        subprocess.run(cmd, check=True)
        print(f"  ✓ VM {vm['name']} installée avec autoinstall")

    def create_vm(self, vm: Dict):
        """Crée ou configure une VM."""
        if not self.vm_exists(vm['name']):
            self.install_vm(vm)
        else:
            # Créer le XML simplifié pour une VM existante
            template = env.get_template('vm.xml.j2')
            vm_xml = template.render(vm=vm)
            try:
                self.conn.defineXML(vm_xml)
                print(f"  ✓ VM {vm['name']} configurée")
            except libvirt.libvirtError as e:
                print(f"  ✗ Erreur lors de la configuration de la VM {vm['name']}: {e}")
                raise

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

    def deploy_vms(self):
        """Déploie toutes les VMs (création + démarrage)."""
        for vm in self.infra['vms']:
            print(f"Déploiement de la VM {vm['name']}...")
            self.create_vm(vm)
            self.start_vm(vm['name'])

    def _create_disk(self, path: str, size_gb: int):
        """Crée un disque qcow2."""
        if os.path.exists(path):
            print(f"  ! Disque {path} existe déjà, ignoré")
            return
        subprocess.run(['qemu-img', 'create', '-f', 'qcow2', path, f"{size_gb}G"], check=True)
        print(f"  ✓ Disque {path} créé ({size_gb} Go)")

    def _create_cloud_init_iso(self, vm: Dict) -> str:
        """Génère une ISO cloud-init avec un format valide pour autoinstall."""
        iso_path = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloudinit.iso")

        # Écrire meta-data
        meta_data = "\n".join(f"{k}: {v}" for k, v in vm['cloud_init'].get('meta_data', {}).items())
        with open("/tmp/meta-data", "w") as f:
            f.write(meta_data)

        # Utiliser directement user_data du YAML (déjà bien formaté)
        user_data = "#cloud-config\n" + yaml.dump(vm['cloud_init']['user_data'], default_flow_style=False, sort_keys=False)
        with open("/tmp/user-data", "w") as f:
            f.write(user_data)

        # Créer l'ISO
        subprocess.run([
            'genisoimage', '-input-charset', 'utf-8',
            '-output', iso_path,
            '-volid', 'cidata', '-joliet', '-rock',
            '/tmp/meta-data', '/tmp/user-data'
        ], check=True)

        print(f"  ✓ ISO cloud-init générée: {iso_path}")
        return iso_path

    def deploy_firewall(self):
        """Affiche les règles de pare-feu à appliquer manuellement."""
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
        for network in reversed(self.infra['networks']):
            self._clean_network(network)
        print("\n✅ Nettoyage terminé !")

    def _clean_vm(self, vm: Dict):
        """Supprime une VM et ses ressources."""
        print(f"Suppression de la VM {vm['name']}...")
        # Vérifier si la VM existe
        if not self.vm_exists(vm['name']):
            print(f"  ! VM {vm['name']} non trouvée")
            return

        # Récupérer la VM
        domain = self.conn.lookupByName(vm['name'])

        # Arrêter la VM si elle est active
        if domain.isActive():
            domain.destroy()
            print(f"  ✓ VM {vm['name']} arrêtée")

        # Supprimer la définition de la VM
        domain.undefine()
        print(f"  ✓ VM {vm['name']} supprimée")

        # Supprimer les disques
        for disk in vm['cloud_init'].get('disks', [{'name': 'system', 'path': f"{VM_IMAGES_DIR}/{vm['name']}.qcow2"}]):
            if os.path.exists(disk['path']):
                os.remove(disk['path'])
                print(f"  ✓ Disque {disk['path']} supprimé")

        # Supprimer l'ISO cloud-init
        cloud_init_iso = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloudinit.iso")
        if os.path.exists(cloud_init_iso):
            os.remove(cloud_init_iso)
            print(f"  ✓ ISO cloud-init {cloud_init_iso} supprimée")

    def _clean_network(self, network: Dict):
        """Supprime un réseau."""
        print(f"Suppression du réseau {network['name']}...")
        # Vérifier si le réseau existe
        if not any(net.name() == network['name'] for net in self.conn.listAllNetworks()):
            print(f"  ! Réseau {network['name']} non trouvé")
            return

        # Récupérer le réseau
        net = self.conn.networkLookupByName(network['name'])

        # Désactiver le réseau s'il est actif
        if net.isActive():
            net.destroy()
            print(f"  ✓ Réseau {network['name']} désactivé")

        # Supprimer la définition du réseau
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

def password_hash(password: str, algorithm: str = 'sha512') -> str:
    import crypt
    return crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

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
