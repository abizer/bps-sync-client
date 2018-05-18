#!./venv/bin/python

from datetime import datetime
import configparser
import inotify.adapters
import os
import sys
import libtmux
from textwrap import dedent
import time


ENV = os.environ.get('BPS_SYNC_ENV', 'dev')
CONF_FILE = os.path.join(
    os.path.dirname(
        os.path.realpath(sys.argv[0])
    ),
    'sync.conf'
)
DEBUG = True if ENV == 'dev' else False


def __debug(text):
    if DEBUG:
        print(text)


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
        os.chmod(filename, 0o700)


def main(watch_dir, tmux_socket, tmux_session, remote_dir, transfer_queue, transfer_log, transfer_script):

    # generate the script we use in tmux to handle the transfer itself
    _build_transfer_script(
        transfer_script, transfer_queue, transfer_log, remote_dir)

    _i = inotify.adapters.Inotify()

    _i.add_watch(watch_dir)

    print("Run Environment: {}".format(ENV))
    print("tmux Socket: {}, Session: {}".format(tmux_socket, tmux_session))
    print("Established watches on {}...".format(watch_dir))

    tmux = libtmux.Server(socket_path=tmux_socket)

    if not tmux:
        print("Could not connect to tmux server on socket {}".format(tmux_socket))
        return 1

    transfer_session = tmux.find_where({"session_name": tmux_session})

    if not transfer_session:
        print("Could not find tmux session {} on socket {}".format(
            tmux_session, tmux_socket))
        return 1

    transfer_script = os.path.abspath(transfer_script)

    for event in _i.event_gen():
        if event is not None:
            (_, type_names, path, filename) = event

            fqfn = os.path.join(path, filename)

            # only interested in moves into the folder
            if "IN_MOVED_TO" in type_names:
                print("{}: received {} for transfer to {}".format(
                    datetime.now(), fqfn, remote_dir))
                try:
                    # execute the transfer script in a tmux window
                    window = transfer_session.new_window(
                        window_shell='{} "{}"'.format(transfer_script, fqfn)
                    )
                    __debug("\twindow: {} {} {}".format(
                        window.id, transfer_script, fqfn))

                except Exception as e:
                    print(e)


if __name__ == '__main__':

    conf = configparser.ConfigParser()
    conf.read(CONF_FILE)

    def _conf(key): return conf.get(ENV, key)

    exit(
        main(
            watch_dir=_conf('watch_dir'),
            tmux_socket=_conf('tmux_socket'),
            tmux_session=_conf('tmux_session'),
            remote_dir=_conf('remote_dir'),
            transfer_queue=_conf('transfer_queue'),
            transfer_log=_conf('transfer_log'),
            transfer_script=_conf('transfer_script'),
        )
    )
