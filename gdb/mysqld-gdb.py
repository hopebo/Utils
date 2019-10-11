#!/usr/bin/python
from __future__ import print_function # python2.X support
import re

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def gdb_threads():
    if hasattr(gdb, 'selected_inferior'):
        threads = gdb.selected_inferior().threads()
    else:
        threads = gdb.inferiors()[0].threads()
    return threads

def pretty_frame_name(frame_name):
    """omit some stdc++ stacks"""
    pretty_names = (
        ('std::__invoke_impl', ''),
        ('std::__invoke', ''),
        ('std::_Bind', ''),
        ('Runnable::operator()', ''),
        ('std::thread::_Invoker', ''),
        ('std::thread::_State_impl', 'std::thread'),
        ('std::this_thread::sleep_for', 'std..sleep_for'))

    for templ, val in pretty_names:
        if frame_name.startswith(templ):
            return val

    return frame_name

def brief_backtrace(filter_threads):
    frames = ''
    frame = gdb.newest_frame() if hasattr(gdb, 'newest_frame') else gdb.selected_frame()
    while frame is not None:
        frame_name = frame.name() if frame.name() is not None else '??'
        if filter_threads is not None and frame_name in filter_threads:
            return None
        frame_name = pretty_frame_name(frame_name)
        if frame_name:
            frames += frame_name + ','
        frame = frame.older()
    frames = frames[:-1]
    return frames

class ThreadSearch(gdb.Command):
    """find threads given a regex which matchs thread name, parameter name or value"""

    def __init__ (self):
        super (ThreadSearch, self).__init__ ("thread search", gdb.COMMAND_OBSCURE)

    def invoke (self, arg, from_tty):
        pattern = re.compile(arg)
        threads = gdb_threads()
        old_thread = gdb.selected_thread()
        for thr in threads:
            thr.switch()
            backtrace = gdb.execute('bt', False, True)
            matched_frames = [fr for fr in backtrace.split('\n') if pattern.search(fr) is not None]
            if matched_frames:
                print(thr.num, brief_backtrace(None))

        old_thread.switch()

ThreadSearch()

class ThreadOverview(gdb.Command):
    """print threads overview, display all frames in one line and function name only for each frame"""
    # filter Innodb backgroud workers
    filter_threads = (
        # Innodb backgroud threads
        'log_closer',
        'buf_flush_page_coordinator_thread',
        'log_writer',
        'log_flusher',
        'log_write_notifier',
        'log_flush_notifier',
        'log_checkpointer',
        'lock_wait_timeout_thread',
        'srv_error_monitor_thread',
        'srv_monitor_thread',
        'buf_resize_thread',
        'buf_dump_thread',
        'dict_stats_thread',
        'fts_optimize_thread',
        'srv_purge_coordinator_thread',
        'srv_worker_thread',
        'srv_master_thread',
        'io_handler_thread',
        'event_scheduler_thread',
        'compress_gtid_table',
        'ngs::Scheduler_dynamic::worker_proxy'
        )
    def __init__ (self):
        super (ThreadOverview, self).__init__ ("thread overview", gdb.COMMAND_OBSCURE)

    def invoke (self, arg, from_tty):
        threads = gdb_threads()
        old_thread = gdb.selected_thread()
        thr_dict = {}
        for thr in threads:
            thr.switch()
            bframes = brief_backtrace(self.filter_threads)
            if bframes is None:
                continue
            if bframes in thr_dict:
                thr_dict[bframes].append(thr.num)
            else:
                thr_dict[bframes] = [thr.num,]
        thr_ow = [(v,k) for k,v in thr_dict.items()]
        thr_ow.sort(key = lambda l:len(l[0]), reverse=True)
        for nums_thr,funcs in thr_ow:
           print (bcolors.FAIL, ','.join([str(i) for i in nums_thr]),bcolors.ENDC, funcs)
        old_thread.switch()

ThreadOverview()

class ItemListDump(gdb.Command):
    """print List <Item>"""
    def __init__ (self):
        super (ItemListDump, self).__init__ ("mydump_list_item", gdb.COMMAND_OBSCURE)

    def print_element(self, i, info, peval):
        item = info.cast(gdb.lookup_type('Item').pointer())
        if peval:
            print(i, item.cast(item.dynamic_type).dereference())
        else:
            print(i, item.dynamic_type)

        gdb.set_convenience_variable('i%d' % i, item.cast(item.dynamic_type))

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) < 1:
            print("usage: mydump_list_item -a")
            return
        if '-a' in args:
            peval = True
        else:
            peval = False

        item_list = args[0]
        i = 0
        node = gdb.parse_and_eval(item_list)['first']
        end_of_list = gdb.parse_and_eval('end_of_list').address
        while node != end_of_list:
            self.print_element(i, node['info'], peval)
            node = node.dereference()['next']
            i += 1

ItemListDump()
