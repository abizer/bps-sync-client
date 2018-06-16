#!/bin/bash
set -euxo pipefail

source sync.conf

xfer="$1"
uxfer="${xfer##*/}"
MD5=$(echo "$xfer" | md5sum | cut -d' ' -f1)
echo "$MD5 $xfer" >> "$transfer_queue"
echo "$(date) transfer of $xfer started" >> "$transfer_log"
curl -X POST -F "key=$msg_api_key" -F "msg=$uxfer download complete" "$msg_gateway"
rsync -rvP --append --info=progress "$xfer" "$remote_dir"
echo "$(date) transfer of $xfer complete" >> "$transfer_log"
curl -X POST -F "key=$msg_api_key" -F "msg=$uxfer transfer complete" "$msg_gateway"
sed -i "/$MD5/d" "$transfer_queue"
