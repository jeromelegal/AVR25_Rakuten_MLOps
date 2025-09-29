# pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib

import argparse, io, os, sys, time
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_service(sa_json_path: str):
    creds = service_account.Credentials.from_service_account_file(sa_json_path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def find_file_id(service, folder_id: str, name: str) -> Optional[str]:
    """
    Cherche un fichier par nom dans un dossier donné.
    ATTENTION : si doublons de noms, on prend le premier trouvé.
    """
    # q : "'<folder>' in parents and name = '<name>' and trashed = false"
    # Pour éviter l'injection d'apostrophes, on échappe les quotes simples
    safe_name = name.replace("'", "\\'")
    q = f"'{folder_id}' in parents and name = '{safe_name}' and trashed = false"
    res = service.files().list(
        q=q,
        fields="files(id, name, mimeType, size)",
        pageSize=1,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None

def download_file(service, file_id: str, dest_path: Path, chunk_mb: int = 2) -> bool:
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    fh = io.FileIO(str(dest_path) + ".part", "wb")
    downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_mb * 1024 * 1024)

    done = False
    try:
        while not done:
            status, done = downloader.next_chunk()
            print(f"Progress {int(status.progress()*100)}%")
        fh.close()
        os.replace(str(dest_path) + ".part", str(dest_path))
        return True
    except Exception:
        fh.close()
        try:
            os.remove(str(dest_path) + ".part")
        except Exception:
            pass
        raise

def main(argv=None):
    import argparse, os
    p = argparse.ArgumentParser(description="Télécharger des images d'un dossier Google Drive à partir d'une liste de noms.")
    p.add_argument("--service-account", required=True, help="Chemin vers la clé JSON du compte de service (sa_key.json)")
    p.add_argument("--folder-id", required=True, help="ID du dossier Drive contenant les images")
    p.add_argument("--names-file", required=True, help="Fichier texte avec un nom par ligne")
    p.add_argument("--dest-dir", required=True, help="Dossier local de destination")
    p.add_argument("--limit", type=int, default=50, help="Nombre max à télécharger lors de cette exécution (défaut: 50)")
    p.add_argument("--sleep", type=float, default=0.0, help="Pause en secondes entre fichiers (optionnel)")
    p.add_argument("--ext", default="", help="Extension à forcer si tes noms n'en ont pas (ex: .jpg). Laisse vide sinon.")
    p.add_argument("--offset", type=int, default=0, help="Nombre de lignes à ignorer au début de names-file (défaut: 0)")
    args = p.parse_args(argv)

    dest_dir = Path(args.dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    service = get_service(args.service_account)

    # Charge la liste de noms
    with open(args.names_file, "r", encoding="utf-8") as f:
        names_all = [line.strip() for line in f if line.strip()]

    # Applique l'offset
    if args.offset < 0:
        raise ValueError("--offset doit être >= 0")
    if args.offset >= len(names_all):
        print(f"Rien à faire: offset={args.offset} >= nb_lignes={len(names_all)}")
        return 0
    names = names_all[args.offset:]  # on coupe la tête puis on traitera 'limit'

    count = 0
    ok, ko, skip = 0, 0, 0

    for name in names:
        if args.ext and not name.lower().endswith(args.ext.lower()):
            candidate = name + args.ext
        else:
            candidate = name

        out_path = dest_dir / candidate

        # Skip si déjà présent (utile si tu ne vides pas le tampon)
        if out_path.exists():
            print(f"↩️  SKIP {candidate} (déjà téléchargé)")
            skip += 1
        else:
            try:
                file_id = find_file_id(service, args.folder_id, candidate)
                if not file_id:
                    print(f"❌ Introuvable dans le dossier: {candidate}")
                    ko += 1
                else:
                    download_file(service, file_id, out_path)
                    print(f"✅ {candidate}")
                    ok += 1
                    count += 1
            except HttpError as e:
                print(f"❌ {candidate}: HttpError {getattr(e, 'status_code', '?')} {getattr(e, 'error_details', e)}")
                ko += 1
            except Exception as e:
                print(f"❌ {candidate}: {e}")
                ko += 1

            if args.sleep > 0:
                time.sleep(args.sleep)

        # On respecte la limite sur le nombre de téléchargements réussis
        if count >= args.limit:
            break

    print(f"\nRésumé: OK={ok}  SKIP={skip}  KO={ko}  (offset={args.offset}, limite={args.limit})")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())