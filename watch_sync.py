#!/usr/bin/env python

import configparser
import inotify.adapters

ENV="dev" # or "prod"
CONF_FILE = 'sync.conf'


def main(watch_dir, tmux_socket, tmux_session, remote_dir, transfer_queue, transfer_log):
    print watch_dir, tmux_socket, tmux_session, remote_dir, transfer_queue, transfer_log
    
    _i = inotify.adapters.Inotify()

    _i.add_watch(watch_dir)
    
    print "Established watches on {}...".format(watch_dir)

    for event in _i.event_gen():
        if event is not None:
            (_, type_names, path, filename) = event

            if "IN_MOVED_TO" in type_names:
                print "path={}, filename={}, type_names={}".format(path, filename, type_names)

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
            transfer_log = conf.get(ENV, 'transfer_log')
        )
    )
