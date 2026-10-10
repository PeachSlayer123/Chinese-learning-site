#!/bin/sh
# Maakt een veilige kopie van data/app.db (ook terwijl de app draait) en houdt de laatste 14.
# Draait elke nacht via cron (zie deploy/README.md). Handmatig: sh deploy/backup.sh
set -eu

cd "$(dirname "$0")/.."
mkdir -p data/backups
naam="app-$(date +%Y-%m-%d_%H%M).db"

# SQLite's eigen backup-functie, in de container (op de Pi zelf staat geen sqlite3).
docker exec chinees python -c "
import sqlite3
bron = sqlite3.connect('/data/app.db')
doel = sqlite3.connect('/data/backups/$naam')
bron.backup(doel)
doel.close(); bron.close()
"

ls -1t data/backups/app-*.db | tail -n +15 | xargs -r rm --
echo "Backup: data/backups/$naam"
