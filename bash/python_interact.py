#!/usr/bin/env python

import sys
import subprocess
import xml.etree.ElementTree as ET
import MySQLdb
import time
import os.path

# database connection parameters
region_metadbs = [
    ('public',
     "127.0.0.1",
     3306,
     "user",
     "password",
     "db")
]

current_metadbs = None
batch_skip_errnos = (1032, 1062, 1397)
# common functions
def print_error(s):
    print(s.center(80))

def run_ssh(ip, cmd, get_output=False):
    cmd_text = "ssh -q -t %s" % ip
    if cmd:
        cmd_text += " " + cmd
    if not get_output:
        subprocess.call(cmd_text, shell=True)
    else:
        return subprocess.check_output(cmd_text, shell=True)

def run_ssh_docker(ip, instantname, get_output=False):
    cmd_text_ssh = "ssh -q -t %s" % ip
    cmd_text = cmd_text_ssh
    cmd_text += " docker exec -it $(%s docker ps | grep %s | awk '{print $1}') bash" % (cmd_text_ssh, instantname)
    if not get_output:
        subprocess.call(cmd_text, shell=True)
    else:
        return subprocess.check_output(cmd_text, shell=True)

def run_my(ip, port, user, cmd, get_output=False):
    mycmd = "mysql --prompt=\\'mysql\\\p:\\\\v\> \\' --default-character-set=utf8mb4 -c -A -u%s -h127.0.0.1 -P%s" % (user, port)
    if cmd:
        mycmd += ' -e "\\"{command}\\""'.format(command = cmd)

    if get_output:
        mycmd += " -X"

    return run_ssh(ip, mycmd, get_output)

def get_field_value(xmlroot, field_name):
    return xmlroot.find('.//field[@name="%s"]' % field_name).text

def slave_skip_gtid(ip, port, user, set_parallel_workers, check_sql_errno):
    def filter_xml_output(xml):
        pos = xml.find('<?xml version="1.0"?>')
        if pos == -1:
            print_error('Error: got a wrong mysql output, %s' % xml)
            return ''
        return xml[pos:]
    xml_output_str = filter_xml_output(run_my(ip, port, user, "show slave status for channel''", True))
    sql_running = get_field_value(ET.fromstring(xml_output_str), "Slave_SQL_Running")
    if sql_running == 'Yes':
        print_error("Could not skip gtid, SQL thread is running")
        return False

    if set_parallel_workers:
        run_my(ip, port, user, "set global slave_parallel_workers=0; start slave sql_thread for channel ''")

    xml_output_str = filter_xml_output(run_my(ip, port, user, "show slave status for channel ''", True))
    slave_status_xml = ET.fromstring(xml_output_str)

    if get_field_value(slave_status_xml, "Slave_SQL_Running") == 'Yes':
        print_error("Could not skip gtid, SQL thread is running")
        return False

    if check_sql_errno:
        sql_errno = int(get_field_value(slave_status_xml, "Last_SQL_Errno"))
        if sql_errno not in batch_skip_errnos:
            print_error("Could not skip gtid, batch skip does not Last_SQL_Errno(%d), current supported errnos: %s" %
                        (sql_errno, ','.join([str(err) for err in batch_skip_errnos])))
            return False

    error_gtid = get_field_value(slave_status_xml, "Last_SQL_Error_Gtid")
    if not error_gtid:
        print_error("Could not skip gtid, Fail to get last sql error gtid")
        return False
    print_error("SKIP GTID: %s" % error_gtid)
    run_my(ip, port, user, "set session gtid_next='%s';begin;commit;set gtid_next='AUTOMATIC';start slave sql_thread for channel ''" % error_gtid)
    return True

def batch_slave_skip_gtid(ip, port, user):
    try:
        if not slave_skip_gtid(ip, port, user, True, True):
            return
        time.sleep(0.1)

        while slave_skip_gtid(ip, port, user, False, True):
            time.sleep(0.1)
    except KeyboardInterrupt:
        return
    # Ctrl-C can be catched by remote shell
    except subprocess.CalledProcessError:
        return

def run_command_in_instances(instances, cmd):
    for instance in instances:
        run_my(instance.ip, instance.port, instance.get_login_user(), cmd)

class ExitSession(Exception):
    pass

class BackAction(Exception):
    pass

def do_exit_session():
    raise ExitSession()

class Instance(object):
    """itype 0: INS_TYPE_CUSTINS
                INS_TYPE_READ = 3
                INS_TYPE_READ_BACKUP = 4

       category: enterprise
    """
    mysql_datadir = '/mysql/mydata'
    def __init__(self, iid, name, itype, ip, port, role, db_type, db_version, category):
        self.iid = iid
        self.name = name
        self.ip = ip
        self.port = port
        self.role = role
        self.itype = itype
        self.db_type = db_type
        self.db_version = db_version
        self.category = category
        self.insinfo_read = False
        self.insinfo = {}

    def read_insinfo(self):
        if self.insinfo_read:
            return

        self.insinfo_read = True
        cmd_get_insinfo = 'cat {home}/insinfo'.format(home = self.get_home())
        try:
            str_insinfo = self.run_shell_command(cmd_get_insinfo).strip()
            self.insinfo = dict(map(lambda i: i.split('='), str_insinfo.split('\r\n')))
        except:
            pass

    def get_insinfo_item(self, key, default_val = None):
        return self.insinfo[key] if self.insinfo.has_key(key) else default_val

    def get_menu_title(self):
        return self.name.ljust(32) + " || " + self.ip.ljust(15) + " || " + str(self.port).ljust(4) + " || " + \
            ("RO" if self.itype == 3 or self.itype == 4 else self.role)

    def run_shell_command(self, cmd, get_output = True):
        return run_ssh(self.ip, cmd, get_output)

    def get_login_user(self):
        default_user = 'root'
        self.read_insinfo()
        return self.get_insinfo_item('account', default_user)

    def get_home(self):
        return '/home/mysql/data{port}'.format(port=self.port)

class MenuItem(object):
    def __init__(self, key, instance, title, action):
        # key is a string list to support alias
        self.key = key
        self.instance = instance
        self.title = title
        self.action = action

    def get_title(self):
        return self.title

    def do_action(self):
        self.action()

    def display(self):
        print '|'.join(self.key) + ')', self.get_title()

class Menu(object):
    def __init__(self, menuitems, prompt):
        self.menuitems = menuitems
        # add back menu
        def do_back_action():
            raise BackAction()
        self.menuitems.append(MenuItem(['a','..'], None, 'Back', do_back_action))

        self.menuitems.append(MenuItem('q', None, 'Find new instances', do_exit_session))
        self.prompt = prompt

    def display(self):
        for mi in self.menuitems:
            mi.display()

    def trigger_action(self, key):
        # hot key for first item
        if not key:
            self.menuitems[0].do_action()
            return

        for mi in self.menuitems:
            if key in mi.key:
                mi.do_action()
                break
        else:
            print_error("Incorrect input")

    def mainloop(self):
        quit_loop = False
        while True:
            self.display()
            try:
                try:
                    key = raw_input("%s> " % self.prompt)
                except EOFError:
                    print('')
                    raise BackAction() # accept EOF(Ctrl-D) as BackAction

                self.trigger_action(key)
            except BackAction:
                return

def execute_sql(sql, metadb = None):
    if metadb is None:
        metadb = current_metadb
    (region, host, port, user, passwd, db) = metadb
    try:
        conn = MySQLdb.connect(host = host, user = user, port = port,
                               passwd = passwd, db = db)
    except MySQLdb.OperationalError, (err, msg):
        print 'wrong metadb configuration for %s' % region
        raise
    cursor = conn.cursor()
    cursor.execute(sql)
    records = cursor.fetchall()
    conn.close()

    return records

def run_instances_menu(sql, prompt):
    instances = execute_sql(sql)

    menuitems = []
    for index, (iid, itype, ip, port, role, insname, db_type, db_version, category) in enumerate(instances):
        instance = Instance(iid, insname, itype, ip, port, role, db_type, db_version, category)

        def createfunc(inst):
            return lambda: run_instance_actions_menu(inst)
        menuitems.append(MenuItem(str(index + 1), instance, instance.get_menu_title(), createfunc(instance)))

    if not menuitems:
        print_error("No instances found")
        return
    # print region
    print("Region: %s" % current_metadb[0])
    # add menuitems for multiple instances
    instances = map(lambda mi: mi.instance, menuitems)
    def createfunc(ins, cmd):
        return lambda: run_command_in_instances(ins, cmd)
    menuitems.append(MenuItem('s', None, 'Show Slave Status', createfunc(instances, 'show slave status\\G')))
    menuitems.append(MenuItem('g', None, 'Show global gtid_executed', createfunc(instances, 'select @@global.gtid_executed')))
    if filter(lambda ins: ins.category == 'enterprise', instances):
        menuitems.append(MenuItem('f', None, 'Show Failover Status', createfunc(instances, 'show failover status')))
    menu = Menu(menuitems, prompt)
    menu.mainloop()

def get_physical_insts_sql(sql_filter):
    sql = """
SELECT id, ins_type, ip, port, role, ins_name, db_type, db_version, category
FROM meta_info WHERE %s
    """ % sql_filter
    return sql

def list_ro_instances(main_id, main_instname):
    cond = 'ins_type = 1' % main_id
    sql = get_physical_insts_sql(cond)
    run_instances_menu(sql, "%s(RO)" % main_instname)

def list_primary_instances(ro_id, ro_instname):
    cond = 'c.id = (select primary_id from meta_info where id = %d)' % ro_id
    sql = get_physical_insts_sql(cond)

    run_instances_menu(sql, "%s(Primary)" % ro_instname)

def run_top(ins):
    cmd = "'top -p `cat {home}/mysql{port}/*.pid`'".format(home = ins.get_home(), port = ins.port)
    ins.run_shell_command(cmd, False)

def view_mysql_log(ins):
    log_root = ins.get_home()
    if ins.db_type.find('mysql') >= 0:
        ins.read_insinfo()
        insid = ins.get_insinfo_item('insid', str(ins.iid))
        log_root = os.path.join(Instance.mysql_datadir, insid, 'log')
    cmd = "'less {root}/mysql/master-error.log'".format(root = log_root)
    ins.run_shell_command(cmd, False)

def run_instance_actions_menu(instance):
    menuitems = []
    # Login and change to instance data directory
    menuitems.append(MenuItem('l', instance, "Login", lambda: run_ssh(instance.ip, '"cd %s; bash --login"' % instance.get_home())))
    menuitems.append(MenuItem('d', instance, "Docker", lambda: run_ssh_docker(instance.ip, instance.name)))
    menuitems.append(MenuItem('t', instance, "Top", lambda: run_top(instance)))
    menuitems.append(MenuItem('m', instance, "My", lambda: run_my(instance.ip, instance.port, instance.get_login_user(), '')))
    menuitems.append(MenuItem('L', instance, "View master-error.log", lambda: view_mysql_log(instance)))
    menuitems.append(MenuItem('s', instance, "Show Slave Status", lambda: run_my(instance.ip, instance.port, instance.get_login_user(), 'show slave status\\G')))
    # Add these menus for all instance types because dual replication for custom instance
    menuitems.append(MenuItem('k', instance, "Skip Error Gtid", lambda: slave_skip_gtid(instance.ip, instance.port, instance.get_login_user(), True, False)))
    menuitems.append(MenuItem('b', instance, "Skip Error Gtid in Batch", lambda: batch_slave_skip_gtid(instance.ip, instance.port, instance.get_login_user())))

    if instance.itype == 0:     # primary instance
        menuitems.append(MenuItem('r', instance, "List read only instances", lambda: list_ro_instances(instance.iid, instance.name)))
    elif instance.itype == 3 or instance.itype == 4: # read only or read only backup instance
        menuitems.append(MenuItem('p', instance, "Find primary instance", lambda: list_primary_instances(instance.iid, instance.name)))
    menu = Menu(menuitems,
                "%s(%s:%d)(%s)" % (instance.name, instance.ip, instance.port, instance.role))
    menu.mainloop()

def get_insts_search_sql(cond, insname_or_id, metadbs):
    sql = 'select id, character_type from meta_info where %s limit 1' % cond
    for metadb in metadbs:
        insts = execute_sql(sql, metadb)
        if insts:
            global current_metadb
            current_metadb = metadb
            break
    else:
        print_error("No instances found")
        return None

    if insts[0][1] == 'logic':
        cond = 'c.parent_id = {insid}'.format(insid = insts[0][0])

    return get_physical_insts_sql(cond)

def search_instances(insname_or_id, metadbs):
    insname_or_id = insname_or_id.strip()
    try:
        insid = int(insname_or_id)
        cond = 'id = %d' % insid
    except ValueError:
        cond = "ins_name = '%s'" % insname_or_id

    sql = get_insts_search_sql(cond, insname_or_id, metadbs)
    if sql is not None:
        run_instances_menu(sql, insname_or_id.strip())

def main():
    while True:
        try:
            try:
                insname_or_id = raw_input("> ")
            except EOFError:
                insname_or_id = 'q'

            if insname_or_id == 'q':
                break

            search_instances(insname_or_id, region_metadbs)
        except ExitSession:
            pass
        except KeyboardInterrupt:
            break

    return 0

if __name__ == '__main__':
    sys.exit(main())