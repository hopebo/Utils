#!/usr/bin/python
from __future__ import print_function

cplus_trivial_frame = ("std::__invoke", # Thread and function calling frames
                       "std::_Bind",
                       "std::__future_base",
                       "std::_Function_handler",
                       "std::function",
                       "std::call_once",
                       "__pthread_once",
                       "std::packaged_task",
                       "std::thread",
                       "__gthread_once")

mysql_trivial_frame = ("log_closer", # Innodb backgroud threads
                       "buf_flush_page_coordinator_thread",
                       "log_writer",
                       "log_flusher",
                       "log_write_notifier",
                       "log_flush_notifier",
                       "log_checkpointer",
                       "lock_wait_timeout_thread",
                       "srv_error_monitor_thread",
                       "srv_monitor_thread",
                       "buf_resize_thread",
                       "buf_dump_thread",
                       "dict_stats_thread",
                       "fts_optimize_thread",
                       "srv_purge_coordinator_thread",
                       "srv_worker_thread",
                       "srv_master_thread",
                       "io_handler_thread",
                       "event_scheduler_thread",
                       "compress_gtid_table",
                       "ngs::Scheduler_dynamic::worker_proxy")

def is_trivial_frame(name):
    return name.startswith(cplus_trivial_frame)

def is_trivial_thread(name):
    return name.startswith(mysql_trivial_frame)

"""
Ignore trivial frames to make backtrace output concise
"""
class TrivialFrameFilter():

    def __init__(self):
        self.name = "TrivialFrameFilter"
        self.priority = 100
        self.enabled = True
        gdb.frame_filters[self.name] = self

    def filter(self, frame_iter):
        return SkipTrivialIterator(frame_iter)

class SkipTrivialIterator:
    def __init__(self, ii):
        self.input_iterator = ii

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            frame = next(self.input_iterator)

            name = str(frame.inferior_frame().name())
            if not is_trivial_frame(name):
                return frame
    # Python 2.x compatibility
    next = __next__

TrivialFrameFilter()

'''
Thread printing utility.
'''
class Colors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def gdb_threads():
    if hasattr(gdb, 'selected_inferior'):
        threads = gdb.selected_inferior().threads()
    else:
        threads = gdb.inferiors()[0].threads()
    return threads

def brief_backtrace():
    frame_brief = ""
    frame = gdb.newest_frame() if hasattr(gdb, 'newest_frame') \
        else gdb.selected_frame()

    while frame is not None:
        frame_name = frame.name() if frame.name() is not None else "??"

        if is_trivial_thread(frame_name):
            return None

        if not is_trivial_frame(frame_name):
            frame_brief += frame_name + ','

        frame = frame.older()

    return frame_brief[:-1]

'''
GDB thread search command.

Find threads given a regex which matchs thread name, parameter name or value.
'''
class ThreadSearch(gdb.Command):
    def __init__ (self):
        super(self.__class__, self).__init__("thread search",
                                             gdb.COMMAND_OBSCURE)

    def invoke (self, arg, from_tty):
        pattern = re.compile(arg)
        threads = gdb_threads()

        current_thread = gdb.selected_thread()

        for thr in threads:
            thr.switch()
            backtrace = gdb.execute('bt', False, True)

            matched_frames = [fr for fr in backtrace.split('\n') \
                              if pattern.search(fr) is not None]
            if matched_frames:
                print(Colors.RED, thr.num, Colors.END, brief_backtrace())

        current_thread.switch()

ThreadSearch()

'''
GDB thread overview command.

Print threads overview, display all frames in one line and function name only
for each frame.
'''
class ThreadOverview(gdb.Command):

    def __init__ (self):
        super(self.__class__, self).__init__("thread overview",
                                             gdb.COMMAND_OBSCURE)

    def invoke (self, arg, from_tty):
        threads = gdb_threads()

        current_thread = gdb.selected_thread()

        thr_dict = {}
        for thr in threads:
            thr.switch()
            brief = brief_backtrace()

            if brief is None:
                continue

            if brief in thr_dict:
                thr_dict[brief].append(thr.num)
            else:
                thr_dict[brief] = [thr.num]

        thr_overview = [(v,k) for k,v in thr_dict.items()]
        thr_overview.sort(key = lambda l:len(l[0]), reverse=True)

        for thr_nums, brief in thr_overview:
            print(Colors.RED, ','.join([str(i) for i in thr_nums]),
                  Colors.END, brief)

        current_thread.switch()

ThreadOverview()
