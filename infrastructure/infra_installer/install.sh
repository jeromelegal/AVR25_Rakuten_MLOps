#!/bin/bash

# Script pour désactiver IPv6 sur Ubuntu (permanent)

# Vérifier si l'utilisateur est root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root. Utilise sudo." >&2
    exit 1
fi

# Désactiver IPv6 via sysctl
echo "Désactivation d'IPv6 via sysctl..."
echo "net.ipv6.conf.all.disable_ipv6=1" >> /etc/sysctl.conf
echo "net.ipv6.conf.default.disable_ipv6=1" >> /etc/sysctl.conf
echo "net.ipv6.conf.lo.disable_ipv6=1" >> /etc/sysctl.conf

# Appliquer les changements sysctl
sysctl -p
sed -i 's/\(GRUB_CMDLINE_LINUX_DEFAULT="[^"]*\)"/\1 ipv6.disable=1"/' /etc/default/grub

# Vérifier que la virtualisation est activée
grep -E --color "vmx|svm" /proc/cpuinfo

# Installer les paquets KVM, QEMU, libvirt, etc.
sudo apt update
sudo modprobe kvm
sudo mknod /dev/kvm c 10 232
sudo chmod 660 /dev/kvm
sudo chown root:kvm /dev/kvm
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager genisoimage

# Ajouter l'utilisateur actuel aux groupes kvm et libvirt
sudo usermod -aG kvm,libvirt $USER
newgrp libvirt

# Créer les répertoires
sudo mkdir -p /var/lib/libvirt/{isos,images,cloud_init_isos}
sudo chown -R $USER:$USER /var/lib/libvirt/{isos,images,cloud_init_isos}

# Vérifier le statut de libvirtd
systemctl status libvirtd
# Démarrer libvirtd
sudo systemctl start libvirtd






# Installer Python et pip (si ce n'est pas déjà fait)
sudo apt install -y python3 python3-pip

# Installer FastAPI et Uvicorn (serveur ASGI)
pip install --break-system-packages fastapi[all] uvicorn libvirt-python pycloudlib PyYAML Jinja2




# Installer Node.js (version LTS recommandée)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Installer Vue CLI
sudo npm install -g @vue/cli



mkdir -p projet/backend projet/frontend projet/scripts
cd projet



pip install  --break-system-packages uvicorn pyyaml


cd ~/projet/frontend
npx create-react-app hyperviseur
cd hyperviseur
npm install axios



# Vérifie qu'un argument (utilisateur) est passé
if [ $# -eq 0 ]; then
    echo "Erreur : Aucun utilisateur spécifié."
    echo "Usage : $0 <utilisateur>"
    exit 1
fi

USERNAME="$1"

# Vérifie que l'utilisateur existe sur la machine
if ! id "$USERNAME" &>/dev/null; then
    echo "Erreur : L'utilisateur '$USERNAME' n'existe pas sur cette machine."
    exit 1
fi

# Crée les répertoires et copie les fichiers
sudo mkdir -p ~/isos
sudo mkdir -p /var/lib/libvirt/isos
sudo mkdir -p /var/lib/libvirt/images
sudo mkdir -p /var/lib/libvirt/cloud_init_isos
sudo cp -R isos/* /var/lib/libvirt/isos/
sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/isos
sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/images
sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/cloud_init_isos

echo "Répertoires créés et permissions mises à jour pour l'utilisateur $USERNAME."

mkdir -p ~/qemu_boot

sudo cp /boot/vmlinuz-$(uname -r) ~/qemu_boot/
sudo cp /boot/initrd.img-$(uname -r) ~/qemu_boot/

sudo chown -R "$USERNAME:$USERNAME" ~/qemu_boot/

sudo chmod u+rw ~/qemu_boot/vmlinuz-*
sudo chmod u+rw ~/qemu_boot/initrd.img-*
sudo chmod u+rw ~/qemu_boot/*


sudo mkdir -p /var/lib/libvirt/shared

sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/shared

sudo chmod 666 /var/lib/libvirt/shared


sudo usermod -aG kvm $USERNAME





sudo apt-get update
sudo apt-get install -y swtpm swtpm-tools

sudo mkdir -p /var/lib/swtpm-localca
sudo chown -R tss:tss /var/lib/swtpm-localca
sudo chmod 0750 /var/lib/swtpm-localca