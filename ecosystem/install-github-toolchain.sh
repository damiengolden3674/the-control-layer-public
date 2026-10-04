#!/bin/sh
set -eu
# Control Layer governed GitHub-sourced toolchain. Installs only approved capability gaps.
# Human remains authoritative; this script never changes hierarchy, identity, privileges, or production policy.
if [ "$(id -u)" -ne 0 ]; then echo "Run with sudo." >&2; exit 2; fi
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ripgrep fd-find fzf btop tmux sysstat smartmontools fio restic rclone ethtool usbutils lm-sensors lynis auditd
install_github_release() {
  repo="$1"; tag="$2"; asset="$3"; binary="$4"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT INT TERM
  cd "$tmp"
  base="https://github.com/$repo/releases/download/$tag"
  curl -fsSLO "$base/$asset"
  curl -fsSLO "$base/$(curl -fsSL "https://api.github.com/repos/$repo/releases/tags/$tag" | jq -r '.assets[] | select(.name | contains("checksums.txt")) | .name' | head -1)"
  checksum_file="$(find . -name '*checksums*.txt' -print -quit)"
  grep " $asset$" "$checksum_file" | sha256sum -c -
  case "$asset" in
    *.tar.gz) tar -xzf "$asset"; install -m 0755 "$binary" "/usr/local/bin/$binary" ;;
    *) install -m 0755 "$asset" "/usr/local/bin/$binary" ;;
  esac
  cd /
  rm -rf "$tmp"
  trap - EXIT INT TERM
}
install_github_release aquasecurity/trivy v0.75.0 trivy_0.75.0_Linux-ARM64.tar.gz trivy
install_github_release anchore/syft v1.54.0 syft_1.54.0_linux_arm64.tar.gz syft
install_github_release anchore/grype v0.120.0 grype_0.120.0_linux_arm64.tar.gz grype
tmp="$(mktemp -d)"
curl -fsSL https://github.com/sigstore/cosign/releases/download/v3.1.3/cosign-linux-arm64 -o "$tmp/cosign-linux-arm64"
curl -fsSL https://github.com/sigstore/cosign/releases/download/v3.1.3/cosign_checksums.txt -o "$tmp/cosign_checksums.txt"
(cd "$tmp" && grep " cosign-linux-arm64$" cosign_checksums.txt | sha256sum -c -)
install -m 0755 "$tmp/cosign-linux-arm64" /usr/local/bin/cosign
rm -rf "$tmp"
echo "GOVERNED_TOOLCHAIN_READY"
