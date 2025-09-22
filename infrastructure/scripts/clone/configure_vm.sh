#!/bin/bash

# Fonction pour configurer les serveurs DNS
configure_dns() {
    echo "Configuration des serveurs DNS..."
    echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
    echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
    echo "Serveurs DNS configurés"
}


# Fonction pour tester la connectivité Internet
test_internet() {
    echo "Test de la connectivité Internet..."
    if ping -c 4 google.com &> /dev/null; then
        echo "Connexion Internet OK"
        return 0
    else
        echo "Erreur: Pas de connexion Internet"
        return 1
    fi
}

# Fonction pour installer yq
install_yq() {
    if ! command -v yq &> /dev/null; then
        echo "Installation de yq..."
        if ! test_internet; then
            echo "Erreur: Impossible de continuer sans connexion Internet"
            exit 1
        fi
        apt-get update
        apt-get install -y wget
        wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq
        chmod +x /usr/bin/yq
        echo "yq installé avec succès"
    else
        echo "yq est déjà installé"
    fi
}



# # Installer yq
# install_yq() {
#     if ! command -v yq &> /dev/null; then
#         echo "Installation de yq..."
#         apt-get update
#         apt-get install -y wget
#         wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq
#         chmod +x /usr/bin/yq
#         echo "yq installé avec succès"
#     else
#         echo "yq est déjà installé"
#     fi
# }

# Installer growpart
install_growpart() {
    if ! command -v growpart &> /dev/null; then
        echo "Installation de growpart..."
        apt-get update
        apt-get install -y cloud-guest-utils
        echo "growpart installé avec succès"
    else
        echo "growpart est déjà installé"
    fi
}

# Chemin vers le fichier YAML dans l'ISO
YAML_FILE="/tmp/clone-init.yaml"

# Fonction pour extraire les valeurs du YAML
get_yaml_value() {
    local key=$1
    yq eval ".$key" "$YAML_FILE"
}

# Monter l'ISO
mount_iso() {
    local iso_path="/dev/sr0"
    local mount_point="/mnt"
    mkdir -p "$mount_point"
    mount "$iso_path" "$mount_point"
    if [ $? -eq 0 ]; then
        echo "ISO montée avec succès"
        # Copier le fichier YAML dans un emplacement temporaire
        cp "$mount_point/clone-init.yaml" "$YAML_FILE"
        umount "$mount_point"
    else
        echo "Erreur lors du montage de l'ISO"
        exit 1
    fi
}

# Agrandir la partition
resize_partition() {
    echo "Agrandissement de la partition..."
    # Détecter le périphérique de disque
    local disk=$(lsblk -d -o NAME -n | grep -v "sr0" | head -n 1)
    if [ -z "$disk" ]; then
        echo "Aucun disque trouvé"
        return 1
    fi

    # Détecter la partition
    local partition="${disk}1"
    if ! lsblk -o NAME | grep -q "$partition"; then
        echo "Aucune partition trouvée sur $disk"
        return 1
    fi

    # Agrandir la partition
    growpart "$disk" 1

    # Vérifier si la partition a été agrandie
    if [ $? -eq 0 ]; then
        echo "Partition agrandie avec succès"
    else
        echo "Erreur lors de l'agrandissement de la partition"
        return 1
    fi

    # Agrandir le système de fichiers
    resize2fs "$partition"
    if [ $? -eq 0 ]; then
        echo "Système de fichiers agrandi avec succès"
    else
        echo "Erreur lors de l'agrandissement du système de fichiers"
        return 1
    fi
}

# Configurer le nom d'hôte
set_hostname() {
    local hostname=$(get_yaml_value "hostname")
    if [ -n "$hostname" ]; then
        hostnamectl set-hostname "$hostname"
        echo "Nom d'hôte configuré à $hostname"
    else
        echo "Aucun nom d'hôte spécifié dans le YAML"
    fi
}

# Configurer les utilisateurs
setup_users() {
    local users=$(get_yaml_value "users")
    if [ -n "$users" ]; then
        for user in $(echo "$users" | yq eval '.[]' -); do
            local username=$(echo "$user" | yq eval '.username' -)
            local password=$(echo "$user" | yq eval '.password' -)
            if [ -n "$username" ] && [ -n "$password" ]; then
                useradd -m "$username"
                echo "$username:$password" | chpasswd
                echo "Utilisateur $username créé avec succès"
            fi
        done
    else
        echo "Aucun utilisateur spécifié dans le YAML"
    fi
}

# Installer les paquets
install_packages() {
    local packages=$(get_yaml_value "packages")
    if [ -n "$packages" ]; then
        apt-get update
        apt-get install -y $packages
        echo "Paquets installés: $packages"
    else
        echo "Aucun paquet spécifié dans le YAML"
    fi
}

# Configurer le réseau
setup_network() {
    local network=$(get_yaml_value "network")
    if [ -n "$network" ]; then
        local interface=$(echo "$network" | yq eval '.interface' -)
        local ip=$(echo "$network" | yq eval '.ip' -)
        local gateway=$(echo "$network" | yq eval '.gateway' -)
        local netmask=$(echo "$network" | yq eval '.netmask' -)
        local dns=$(echo "$network" | yq eval '.dns' -)

        # Configurer l'interface réseau
        cat > /etc/network/interfaces <<EOF
auto $interface
iface $interface inet static
    address $ip
    netmask $netmask
    gateway $gateway
    dns-nameservers $dns
EOF

        # Redémarrer le réseau
        systemctl restart networking
        echo "Réseau configuré pour $interface avec l'adresse IP $ip"
    else
        echo "Aucune configuration réseau spécifiée dans le YAML"
    fi
}

# Exécuter des scripts supplémentaires
run_additional_scripts() {
    local scripts=$(get_yaml_value "additional_scripts")
    if [ -n "$scripts" ]; then
        for script in $scripts; do
            if [ -f "$script" ]; then
                bash "$script"
                echo "Script $script exécuté avec succès"
            else
                echo "Script $script introuvable"
            fi
        done
    else
        echo "Aucun script supplémentaire spécifié dans le YAML"
    fi
}

# Point d'entrée principal
main() {
    configure_dns
    test_internet
    install_yq
    install_growpart
    mount_iso
    resize_partition
    set_hostname
    setup_users
    install_packages
    setup_network
    run_additional_scripts
}

main
