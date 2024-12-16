import subprocess
import threading
import configparser

class WatchDog:
    def __init__(self, watch_path, events=['modify', 'moved_to', 'create']):
        self.watch_path = watch_path
        self.events = events

    def run(self):
        inotify = f"inotifywait -m -r -e {','.join(self.events)} "\
            f"--exclude '/\.' {self.watch_path}"
        print(inotify)

        p = subprocess.Popen(inotify, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        event = p.stdout.readline()
        while event:
            print(event)

            # Do your action
            self.action()

            out = p.stdout.readline()

        if p.poll():
            print(p.stderr.readline())

    def action(self):
        pass

class WatchDogRsync(WatchDog):
    def __init__(self, watch_path, target_path, events=['modify', 'moved_to',
                                                        'create']):
        super().__init__(watch_path, events)
        self.target_path = target_path

    def action(self):
        rsync = f'rsync -azvu {self.watch_path}/ {self.target_path}'
        print(rsync)

        p = subprocess.run(rsync, shell=True, check=True)

# Don't lowercase the key
config = configparser.RawConfigParser()
config.optionxform = lambda option: option
config.read('config.ini')

threads = []

for source, target in config.items('RSYNC'):
    print (f"Watch on {source}, Rsync to {target}")
    dog = WatchDogRsync(source.strip(), target.strip())
    threads.append(threading.Thread(target=WatchDog.run, args=(dog,)))

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
