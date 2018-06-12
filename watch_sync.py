#!./venv/bin/python

from datetime import datetime
import inotify.adapters
import os
import sys
import libtmux
import time

TRANSFER_SCRIPT = 'do_transfer.sh'

CONF_FILE = os.path.join(
    os.path.dirname(
        os.path.realpath(sys.argv[0])
    ),
    'sync.conf'
)


def _schedule_transfer():
    pass


def _acquire_tmux(socket, session):
    """Connect to or create a tmux socket and return a session."""

    tmux = libtmux.Server(socket_path=socket)
    if tmux.find_where({'session_name': session}):
        transfer_session = tmux.find_where({"session_name": session})
    else:
        transfer_session = tmux.new_session(session_name=session)

    return transfer_session


def _watch_dir(watch):
    """Establish a watch for moves into the desired directory."""

    _i = inotify.adapters.Inotify()
    _i.add_watch(watch)

    def do_watch():
        for event in _i.event_gen():
            if event is not None:
                (_, type_names, path, filename) = event
                if "IN_MOVED_TO" in type_names:
                    yield path, filename

    return do_watch


def main(transfer_script, transfer_session, watched_dir):
    """Trigger an rsync in a tmux window for files moved into the watch."""

    for path, filename in watched_dir():
        fqfn = os.path.join(path, filename)

        print("{}: received {} for transfer".format(
            datetime.now().strftime("%x %X"), fqfn))

        try:
            window = transfer_session.new_window(
                window_shell='{} "{}"'.format(transfer_script, fqfn)
            )

        except Exception as e:
            print(e)


if __name__ == '__main__':

    # hacky config that can also be sourced by a bash script
    config = {}
    with open(CONF_FILE, 'r') as conf:
        for line in conf.readlines():
            k, v = line.strip().split('=')
            config[k] = v

    transfer_script = os.path.abspath(TRANSFER_SCRIPT)
    transfer_session = _acquire_tmux(
        config['tmux_socket'],
        config['tmux_session']
    )
    watch_fn = _watch_dir(config['watch_dir'])

    print("Established watches on '{}'".format(
        os.path.abspath(config['watch_dir'])))
    print("Remote transfer directory is {}".format(config['remote_dir']))

    exit(
        main(
            transfer_script=transfer_script,
            transfer_session=transfer_session,
            watched_dir=watch_fn
        )
    )
