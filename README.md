<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/silica-logo-dark.svg">
    <img alt="Silica" src=".github/silica-logo-light.svg" width="200">
  </picture>
</p>

<h1 align="center">silica-packages</h1>

<p align="center">
  <b>Silica packages for Fedora.</b><br>
  The desktop, the apps, Inter and silica-icons as RPMs, with a Wayland session you can pick at login.
</p>

<p align="center">
  <img alt="Fedora: RPM" src="https://img.shields.io/badge/Fedora-RPM-51A2DA?style=flat-square&logo=fedora">
  <img alt="status: planned" src="https://img.shields.io/badge/status-planned-8a8a8a?style=flat-square">
</p>

The first step towards the distribution: Silica installable on any Fedora, without
reinstalling. The same specs feed the image of [`silica-os`](https://github.com/silica-linux/silica-os).

## To do

- RPM specs for every component, built in CI and published (COPR);
- the session entry (`wayland-sessions/silica.desktop`) starting Ossido with the shell, the
  daemon and the portals;
- versions aligned with the tags of the source repositories.
