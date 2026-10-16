
#!/bin/sh
set -eu

DIR="monitoring/node-exporter/textfile"
OUTPUT="$DIR/disk.prom"
TMP="$DIR/disk.prom.tmp"

mkdir -p "$DIR"

df -B1 / | awk '
NR == 2 {
    print "custom_disk_size_bytes " $2
    print "custom_disk_used_bytes " $3
    print "custom_disk_available_bytes " $4
    if ($2 > 0) {
        printf "custom_disk_used_percent %.2f\n", 100 * $3 / $2
    }
}' > "$TMP"

mv "$TMP" "$OUTPUT"

