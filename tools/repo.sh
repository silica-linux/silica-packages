#!/bin/bash
# tools/repo.sh <rpm dir> <repo dir>
#
# A dnf repository from built RPMs: the binary RPMs (not the SRPMs) in <repo dir>, its
# repodata (createrepo_c, in a Fedora container if the host lacks it) and silica.repo
# pointing at it. The default baseurl is a local path, for a repository unpacked from the
# release archive; set BASEURL to publish it somewhere else (GitHub Pages, a web server).
set -euo pipefail

rpms="${1:?rpm dir}"
repo="${2:?repo dir}"
fedora="${FEDORA:-44}"
mkdir -p "$repo"
find "$rpms" -name '*.rpm' ! -name '*.src.rpm' -exec cp -t "$repo" {} +

if command -v createrepo_c >/dev/null; then
  createrepo_c -q "$repo"
else
  container="${CONTAINER:-$(command -v podman >/dev/null && echo podman || echo docker)}"
  # Rootless podman maps the container's root to the caller: no chown (it would hand the
  # files to a sub-uid). Docker runs as the real root: hand them back.
  chown=""
  [ "$(basename "$container")" = docker ] && chown=" && chown -R $(id -u):$(id -g) /repo"
  "$container" run --rm -v "$(cd "$repo" && pwd):/repo:z" \
    "${IMAGE:-registry.fedoraproject.org/fedora:$fedora}" \
    bash -c "dnf -y -q install createrepo_c >/dev/null && createrepo_c -q /repo$chown"
fi

cat >"$repo/silica.repo" <<EOF
[silica]
name=Silica for Fedora \$releasever
baseurl=${BASEURL:-file:///var/lib/silica-repo}
enabled=1
gpgcheck=0
repo_gpgcheck=0
EOF
echo "repo.sh: $(find "$repo" -name '*.rpm' | wc -l) RPMs in $repo"
