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
# sudo modprobe kvm_intel   # Pour les processeurs Intel
# # ou
# sudo modprobe kvm_amd     # Pour les processeurs AMD
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

