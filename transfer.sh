echo 1234 > .dev_transfer_queue
sleep 100
sed '/1234/d' .dev_transfer_queue
