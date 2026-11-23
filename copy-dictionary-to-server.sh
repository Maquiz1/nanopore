#!/bin/bash
#
# Copy the issued data dictionary versions to the server, where the Codebook page offers them for download.
# They are kept out of git (data_dictionary/). Run on your computer, not on the server.
#
# Usage:  ./copy-dictionary-to-server.sh user@server [remote folder]
# The remote folder defaults to nanopore/data_dictionary (next to nanopore/backend in the remote user's home).

set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 1 ]; then
    echo "Usage: $0 user@server [remote folder]" >&2
    exit 1
fi
SERVER="$1"
REMOTE_DIR="${2:-nanopore/data_dictionary}"

shopt -s nullglob
FILES=(data_dictionary/Tanzania_Data_Dictionary_v*.xlsx)
if [ ${#FILES[@]} -eq 0 ]; then
    echo "No dictionary in data_dictionary/. Run in backend/: python manage.py issue_data_dictionary --source <previous version>" >&2
    exit 1
fi

echo "Copying ${#FILES[@]} file(s) to $SERVER:$REMOTE_DIR ..."
ssh "$SERVER" "mkdir -p '$REMOTE_DIR' && chmod 755 '$REMOTE_DIR'"
for FILE in "${FILES[@]}"; do
    NAME=$(basename "$FILE")
    scp -q "$FILE" "$SERVER:$REMOTE_DIR/$NAME.part"
    # Variables, codes and mapping rules only: no participant data.
    ssh "$SERVER" "chmod 644 '$REMOTE_DIR/$NAME.part' && mv '$REMOTE_DIR/$NAME.part' '$REMOTE_DIR/$NAME'"
    echo "  $NAME"
done
echo "Done. The Codebook page now offers them."
