#!/usr/bin/env python

import inotify.adapters

WATCH_DIR="test"

def main():
    _i = inotify.adapters.Inotify()

    _i.add_watch(WATCH_DIR)
    
    print "Established watches on {}...".format(WATCH_DIR)

    for event in _i.event_gen():
        if event is not None:
            (_, type_names, path, filename) = event

            if "IN_MOVED_TO" in type_names:
                print "path={}, filename={}, type_names={}".format(path, filename, type_names)

if __name__ == '__main__':
    exit(main())
