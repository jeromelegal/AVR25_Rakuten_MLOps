#!/bin/bash
# Chemin de départ
BASE_PATH="."
# Tableaux pour stocker les exclusions et les extensions
EXCLUDE_DIRS=()
INCLUDE_EXTS=()
# Fonction pour afficher l'usage
usage() {
    echo "Usage: $0 -e <exclude_dirs> -i <include_exts>"
    echo "Options:"
    echo "  -e  Directories to exclude, separated by commas"
    echo "  -i  File extensions to include, separated by commas"
    echo "Si aucune option n'est fournie, tous les fichiers seront inclus."
}
# Analyse des arguments
while getopts ":e:i:" opt; do
  case $opt in
    e)
      IFS=',' read -ra EXCLUDE_DIRS <<< "$OPTARG"
      ;;
    i)
      IFS=',' read -ra INCLUDE_EXTS <<< "$OPTARG"
      ;;
    \?)
      echo "Option invalide: -$OPTARG" >&2
      usage
      ;;
  esac
done
# Construction de la commande `find`
FIND_CMD="find \"$BASE_PATH\" -type f"
# Ajouter les exclusions
for dir in "${EXCLUDE_DIRS[@]}"; do
    FIND_CMD+=" -not -path \"*/$dir/*\""
done
# Ajouter les inclusions (extensions)
if [ ${#INCLUDE_EXTS[@]} -ne 0 ]; then
    for ext in "${INCLUDE_EXTS[@]}"; do
        FIND_CMD+=" -name \"*.$ext\""
    done
fi
# Ajouter l'option -print0 pour délimiter par un caractère nul
FIND_CMD+=" -print0"
# Exécuter la commande find et traiter chaque fichier trouvé
eval "$FIND_CMD" | while IFS= read -r -d '' file; do
    # Délimitation pour le début d'un fichier
    echo "=============================================="
    echo "Chemin du fichier: $file"
    echo "=============================================="
    # Vérifier si le fichier est un fichier régulier et lisible
    if [ -f "$file" ] && [ -r "$file" ]; then
        echo "Contenu du fichier:"
        cat "$file"
        echo
    else
        echo "Impossible de lire le fichier: $file"
    fi
    # Ajouter une ligne vide et une délimitation pour séparer les fichiers
    echo
done
