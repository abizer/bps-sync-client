#!/usr/bin/env python

from datetime import datetime
import configparser
import inotify.adapters
import os
import libtmux
from textwrap import dedent
import time

ENV="dev" # or "prod"
CONF_FILE = 'sync.conf'

def main(watch_dir, tmux_socket, tmux_session, remote_dir, transfer_queue, transfer_log, transfer_script):

    # generate the script we use in tmux to handle the transfer itself
    _build_transfer_script(transfer_script, transfer_queue, transfer_log, remote_dir)

    _i = inotify.adapters.Inotify()

    _i.add_watch(watch_dir)

    print "Established watches on {}...".format(watch_dir)

    tmux = libtmux.Server(socket_path=tmux_socket)
    transfer_session = tmux.find_where({ "session_name": tmux_session })
    transfer_script = 'transfer.sh' if ENV is "prod" else "dev_transfer.sh"

    for event in _i.event_gen():
        if event is not None:
            (_, type_names, path, filename) = event

            fqfn = os.path.join(path, filename)

            # only interested in moves into the folder
            if "IN_MOVED_TO" in type_names:
                print "{}: received {} for transfer".format(datetime.now(), fqfn)
                try:
                    # execute the transfer script in a tmux session
                    window = transfer_session.new_window(window_shell='bash {} {}'.format(transfer_script, fqfn))
                    while True:
                        print window.id, window.active
                        time.sleep(2)

                except Exception as e:
                    print(e)

def _schedule_transfer():
    pass

def _build_transfer_script(filename, transfer_queue, transfer_log, remote_dir):
    template = dedent("""
    #!/bin/bash
    set -euxo pipefail

    xfer="$1"
    MD5=$(echo "$xfer" | md5sum | cut -d' ' -f1)

    echo "$MD5 $xfer" >> {transfer_queue}
    echo "$(date) transfer of $xfer started" >> {transfer_log}
    rsync -rvP --append --info=progress "$xfer" {remote_dir}
    echo "$(date) transfer of $xfer complete" >> {transfer_log}
    sed -i "/$MD5/d" {transfer_queue}
    """).format(transfer_queue=transfer_queue, transfer_log=transfer_log, remote_dir=remote_dir)

    with open(filename, 'w') as transfer_file:
        transfer_file.write(template)

if __name__ == '__main__':

    conf = configparser.ConfigParser()
    conf.read(CONF_FILE)
    
    exit(
        main(
            watch_dir = conf.get(ENV, 'watch_dir'),
            tmux_socket = conf.get(ENV, 'tmux_socket'),
            tmux_session = conf.get(ENV, 'tmux_session'),
            remote_dir = conf.get(ENV, 'remote_dir'),
            transfer_queue = conf.get(ENV, 'transfer_queue'),
            transfer_log = conf.get(ENV, 'transfer_log'),
            transfer_script = conf.get(ENV, 'transfer_script'),
        )
    )
