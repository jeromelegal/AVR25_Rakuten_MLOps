#!/bin/bash

# Script pour ajouter "hyperviseur" dans /etc/hosts

# Vérifier si l'entrée existe déjà
if ! grep -q "hyperviseur" /etc/hosts; then
    # Ajouter l'entrée avec tee (nécessite sudo)
    echo "Ajout de l'entrée 'hyperviseur' dans /etc/hosts..."
    echo "127.0.0.1   hyperviseur" | sudo tee -a /etc/hosts > /dev/null

    # Vérifier que l'ajout a réussi
    if grep -q "hyperviseur" /etc/hosts; then
        echo "✅ Entrée ajoutée avec succès :"
        grep "hyperviseur" /etc/hosts
    else
        echo "❌ Échec de l'ajout. Vérifiez les permissions."
        exit 1
    fi
else
    echo "ℹ️ L'entrée 'hyperviseur' existe déjà dans /etc/hosts :"
    grep "hyperviseur" /etc/hosts
fi

# Vérifier la résolution
echo -e "\nTest de résolution :"
ping -c 1 hyperviseur