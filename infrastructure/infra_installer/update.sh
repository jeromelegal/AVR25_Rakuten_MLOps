#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Installer libvirt récent (>= 11.5) avec sockets corrects
# Méthode : tarball libvirt 11.7.0 + Meson/Ninja
# Particularité : --localstatedir=/var pour avoir /run/libvirt/*
# Testé sur Ubuntu 24.04 (Noble)
# ------------------------------------------------------------

LIBVIRT_VER="11.7.0"
TARBALL_URL="https://download.libvirt.org/libvirt-${LIBVIRT_VER}.tar.xz"
SRC_ROOT="/usr/local/src/libvirt-src"
PREFIX="/usr/local"               # binaires & libs sous /usr/local
LOCALSTATEDIR="/var"              # sockets sous /run/libvirt/*
BUILD_DIR="build"

log()  { printf "\033[1;34m==>\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err()  { printf "\033[1;31m[ERR]\033[0m %s\n" "$*" >&2; }

ensure_deps() {
  log "Installation des dépendances de build…"
  sudo apt-get update -y
  sudo apt-get install -y \
    build-essential git meson ninja-build pkg-config \
    libglib2.0-dev libxml2-dev libgnutls28-dev libgcrypt20-dev \
    libcap-ng-dev libnl-3-dev libnl-route-3-dev libyajl-dev \
    libcurl4-gnutls-dev libreadline-dev libudev-dev libnuma-dev \
    libpciaccess-dev libparted-dev libpmem-dev libseccomp-dev \
    libsystemd-dev libtirpc-dev librbd-dev libssh2-1-dev libssh-dev \
    xsltproc gettext po4a python3-dev python3-docutils \
    libjson-c-dev jq lsb-release wget
  log "Dépendances OK."
}

download_tarball() {
  log "Préparation du répertoire sources : ${SRC_ROOT}"
  sudo mkdir -p "${SRC_ROOT}"
  sudo chown -R "${USER}:${USER}" "${SRC_ROOT}"
  cd "${SRC_ROOT}"

  if [[ ! -f "libvirt-${LIBVIRT_VER}.tar.xz" ]]; then
    log "Téléchargement de libvirt ${LIBVIRT_VER}…"
    wget -q --show-progress "${TARBALL_URL}"
  else
    log "Tarball déjà présent : libvirt-${LIBVIRT_VER}.tar.xz"
  fi

  rm -rf "libvirt-${LIBVIRT_VER}"
  log "Extraction…"
  tar xf "libvirt-${LIBVIRT_VER}.tar.xz"
  cd "libvirt-${LIBVIRT_VER}"
}

build_install_libvirt() {
  log "Configuration Meson (prefix=${PREFIX}, localstatedir=${LOCALSTATEDIR})…"
  rm -rf "${BUILD_DIR}"
  meson setup "${BUILD_DIR}" \
    --prefix="${PREFIX}" \
    --localstatedir="${LOCALSTATEDIR}" \
    -Ddriver_qemu=enabled \
    -Ddriver_network=enabled \
    -Ddriver_interface=enabled \
    -Ddriver_lxc=disabled \
    -Ddriver_bhyve=disabled \
    -Dinit_script=systemd

  log "Compilation…"
  ninja -C "${BUILD_DIR}"

  log "Installation…"
  sudo ninja -C "${BUILD_DIR}" install

  log "Mise à jour des liens dynamiques…"
  echo -e "${PREFIX}/lib\n${PREFIX}/lib/x86_64-linux-gnu" | sudo tee /etc/ld.so.conf.d/99-local-libvirt.conf >/dev/null
  sudo ldconfig
}

fix_qemu_shadowing() {
  # Si un QEMU custom non exécutable existe sous /usr/local/bin, il peut casser libvirt.
  if [[ -e /usr/local/bin/qemu-system-x86_64 && ! -x /usr/local/bin/qemu-system-x86_64 ]]; then
    warn "qemu-system-x86_64 présent sous /usr/local/bin mais non exécutable (ou FS noexec)."
    warn "On le met de côté pour utiliser celui fourni par Ubuntu."
    sudo mv /usr/local/bin/qemu-system-x86_64 /usr/local/bin/qemu-system-x86_64.bak
  fi
}

configure_systemd() {
  log "Configuration systemd (sockets libvirt modernes)…"
  sudo systemctl daemon-reload || true
  # Arrêter les anciennes unités si présentes
  sudo systemctl stop libvirtd libvirtd.socket virtqemud virtqemud.socket \
    virtqemud-ro.socket virtqemud-admin.socket 2>/dev/null || true
  # Activer les sockets QEMU
  sudo systemctl enable --now virtqemud.socket virtqemud-admin.socket || true
}

ensure_env() {
  # Rendre /usr/local prioritaire pour virsh & libs (session courante + persistant)
  local bashrc="${HOME}/.bashrc"

  if ! grep -q "/usr/local/lib/x86_64-linux-gnu" /etc/ld.so.conf.d/99-local-libvirt.conf 2>/dev/null; then
    echo -e "${PREFIX}/lib\n${PREFIX}/lib/x86_64-linux-gnu" | sudo tee /etc/ld.so.conf.d/99-local-libvirt.conf >/dev/null
    sudo ldconfig
  fi

  if ! grep -q "libvirt (install locale)" "$bashrc" 2>/dev/null; then
    {
      echo ""
      echo "# libvirt (install locale)"
      echo "export LD_LIBRARY_PATH=${PREFIX}/lib:${PREFIX}/lib/x86_64-linux-gnu:\$LD_LIBRARY_PATH"
      echo "export PKG_CONFIG_PATH=${PREFIX}/lib/pkgconfig:${PREFIX}/lib/x86_64-linux-gnu/pkgconfig:\$PKG_CONFIG_PATH"
      echo "export PATH=${PREFIX}/bin:\$PATH"
    } >> "$bashrc"
    warn "Variables d'environnement ajoutées à ~/.bashrc. Ouvre un nouveau shell pour les prendre en compte."
  fi

  # Exports pour la session courante
  export LD_LIBRARY_PATH="${PREFIX}/lib:${PREFIX}/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
  export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig:${PREFIX}/lib/x86_64-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-}"
  export PATH="${PREFIX}/bin:${PATH}"
}

verify_all() {
  log "Vérifications…"
  set +e
  echo "---- virsh version ----"
  virsh version || true
  echo "---- sockets présents ----"
  ls -l /run/libvirt/virtqemud-sock 2>/dev/null || true
  echo "---- which qemu-system-x86_64 ----"
  which qemu-system-x86_64 || true
  echo "---- qemu-system-x86_64 --version ----"
  qemu-system-x86_64 --version 2>/dev/null || true
  echo "---- domcapabilities (nvme) ----"
  virsh domcapabilities --machine pc-q35-6.2 --virttype kvm 2>/dev/null | sed -n '/<diskSupported/,/diskSupported>/p' || true
  set -e

  cat <<'EOF'

Si "virsh version" affiche libvirt 11.x et que le socket /run/libvirt/virtqemud-sock existe,
tu peux utiliser NVMe nativement dans tes XML :

  <controller type='nvme' model='pcie' index='0'/>
  <disk type='file' device='disk'>
    <driver name='qemu' type='qcow2'/>
    <source file='/var/lib/libvirt/images/disk.qcow2'/>
    <target dev='nvme0n1' bus='nvme'/>
    <serial>nvme-disk-1</serial>
  </disk>

Machine type recommandé : q35 (déjà dans ton template).
EOF
}

main() {
  ensure_deps
  download_tarball
  build_install_libvirt
  fix_qemu_shadowing
  configure_systemd
  ensure_env
  verify_all
  log "✅ Installation libvirt ${LIBVIRT_VER} terminée avec --localstatedir=/var (sockets sous /run/libvirt)."
  log "Ouvre un nouveau shell (ou 'source ~/.bashrc') puis re-teste 'virsh version'."
}

main "$@"
