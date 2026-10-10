# Deploy: de app op de Raspberry Pi

De Pi is de **enige plek met data** (`app.db`). Pc, laptop en gsm gebruiken gewoon de site.

## De Pi

| | |
|---|---|
| Toestel | Raspberry Pi 4 Model B, 4 GB RAM, 64 GB SD-kaart |
| OS | Raspberry Pi OS / Debian 13 (trixie), 64-bit |
| Adres thuis | `192.168.1.45`, gebruiker `chunrasppedro` (inloggen met SSH-sleutel) |
| App | `~/chinees` (clone van deze repo), poort **8080** → thuis <http://192.168.1.45:8080> |
| Overal (Tailscale) | **<http://pi:8080>** (werkt), <https://pi.tail99d614.ts.net> (certificaat nog geweigerd, zie meeBezig); Tailscale-IP `100.119.183.20` |
| Ook op de Pi | **Home Assistant** in Docker (`~/homeassistant`: `homeassistant`, `mosquitto`, `matter-server`, poort 8123) |

> ⚠️ **Nooit opnieuw flashen of `~/homeassistant` aanraken.** De Chinees-app is een apart Compose-project (`chinees`).

## Hoe het werkt

- [`../Dockerfile`](../Dockerfile): bouwt de frontend (`npm run build`) en zet die in één image met de backend.
  `FRONTEND_DIR` laat FastAPI de site serveren, dus alles draait op één poort.
- [`docker-compose.yml`](docker-compose.yml): container `chinees`, `restart: unless-stopped` (start vanzelf na een herstart).
  Leest `~/chinees/.env` en bewaart de database in `~/chinees/data/app.db`.
- [`backup.sh`](backup.sh): elke nacht om 03:30 (cron) een kopie naar `~/chinees/data/backups/`, de laatste 14 blijven.

## Dagelijks gebruik (vanaf de pc of laptop)

```sh
ssh chunrasppedro@192.168.1.45
cd ~/chinees

# Nieuwe versie uitrollen (na een push naar main)
git pull && docker compose -f deploy/docker-compose.yml up -d --build

# Status en logs
docker ps
docker logs -f chinees

# Handmatige backup
sh deploy/backup.sh
```

Een backup terugzetten: `docker stop chinees`, het bestand uit `data/backups/` kopiëren naar `data/app.db`, `docker start chinees`.

## Stappenplan (hoe de Pi opgezet is)

1. ✅ Toegang hersteld: wachtwoord gereset via `init=/bin/sh` in `cmdline.txt`, de SSH-sleutel van de pc in
   `~/.ssh/authorized_keys`. Een nieuw toestel (bv. de laptop): eenmalig in PowerShell
   `type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh chunrasppedro@192.168.1.45 "cat >> ~/.ssh/authorized_keys"`
2. ✅ Docker en Compose stonden er al (voor Home Assistant)
3. ✅ `git clone https://github.com/PeachSlayer123/Chinese-learning-site.git ~/chinees`
4. ✅ `.env` van de pc gekopieerd (`scp`, `chmod 600`). Staat niet in git
5. ✅ `docker compose -f deploy/docker-compose.yml up -d --build`. Begonnen met een lege database
6. ✅ Backup-cron: `30 3 * * * sh ~/chinees/deploy/backup.sh >> ~/chinees/data/backup.log 2>&1`
7. ✅ **Tailscale** (2026-10-10): `install.sh`, `sudo tailscale up --hostname=pi`, ingelogd met het Google-account
   van de gebruiker. `sudo tailscale serve --bg 8080` geeft https binnen het eigen netwerk (nodig voor een PWA).
   Elk nieuw toestel: Tailscale installeren en met hetzelfde Google-account inloggen.
   Later eventueel publiek met een eigen domein: Cloudflare Tunnel + Access (voorlopig niet gewenst)
8. ⬜ Backups ook buiten de Pi bewaren (de backups staan nu op dezelfde SD-kaart)

## Na een stroomonderbreking of verhuis

Alles start vanzelf: `docker`, `tailscaled`, `cron` en `ssh` staan op *enabled*, de containers hebben
`restart: unless-stopped` en `tailscale serve --bg` blijft bewaard. Na ±1-2 minuten is de app terug.
Andere wifi of netwerkkabel op de nieuwe plek? Via Tailscale blijft het adres hetzelfde; het thuisadres `192.168.1.45` kan veranderen.

## Notities

- De Pi-kernel ondersteunt geen geheugenlimieten voor containers (`mem_limit` wordt genegeerd).
  De app gebruikt ±135 MB RAM; er blijft ruim genoeg over voor Home Assistant.
- Bestanden in `data/` zijn van `root` (de container schrijft ze). Lezen kan gewoon, verwijderen kan dankzij de map-rechten.
