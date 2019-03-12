import time
import psutil
from proc_info import ProcInfo


def calc_proc_cpu_rate(proc):
    try:
        return proc.cpu_percent()
    except Exception:
        return None

def calc_proc_memory_information(proc):
    try:
        memory = proc.memory_info()
        real_mem = memory.rss / 1024. ** 2
        virtual_mem = memory.vms / 1024. ** 2
        return (real_mem, virtual_mem)
    except Exception:
        return None

def is_proc_alive(proc):
    if proc is None: return False
    try:
        proc_status = proc.status()
    except Exception:
        return False
    if proc_status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
        return False
    return True

def get_subprocesses(proc):
    if not is_proc_alive(proc): return []
    subprocesses = []
    for child in proc.children():
        if not is_proc_alive(child): continue
        subprocesses.append(child)
        subprocesses.extend(get_subprocesses(child))
    return subprocesses

def format_string_to_csv_format(line):
    if ('"' not in line) and ("," not in line): return line
    if '"' in line:
        line = line.replace('"', '""')
    if "," in line:
        line = '"' + line + '"'
    return line

class PsMonitor:
    def __init__(self, pid, monitor_subprocess_is_allowed=False):
        try:
            self.proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            self.proc = None
            raise Exception("process %d is not found!" % pid)
        self.pid = pid
        self.cmdline = " ".join(self.proc.cmdline())
        self.proc_info = ProcInfo()
        self.monitor_subprocess_is_allowed = monitor_subprocess_is_allowed
        self.children_info = {}   ## key: pid+cmdline, value: ProcInfo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.write_to_csv()

    def write_to_csv(self):
        filename = "output_%d.csv" % self.pid
        print("result will write to %s" % filename)
        title_line = "pid,cmdline,max real memory(MB),max virtual memory(MB)\n"
        with open(filename, "w") as fd:
            fd.write(title_line)
            fd.write("%d,%s,%d,%d\n" % (self.pid, format_string_to_csv_format(self.cmdline), self.proc_info.max_real_memory, self.proc_info.max_virtual_memory))
            for subproc_key in self.children_info:
                subproc_info = self.children_info[subproc_key]
                fd.write("%d,%s,%d,%d\n" % (subproc_key[0], format_string_to_csv_format(subproc_key[1]), subproc_info.max_real_memory, subproc_info.max_virtual_memory))

    def run(self):
        while True:
            if not is_proc_alive(self.proc): break
            proc_mem_info = calc_proc_memory_information(self.proc)
            if proc_mem_info is None: break
            proc_real_mem, proc_virtual_mem = proc_mem_info[0], proc_mem_info[1]
            if self.monitor_subprocess_is_allowed:
                subprocesses = get_subprocesses(self.proc)
                total_subproc_real_mem, total_subproc_virtual_mem = 0, 0
                for subprocess in subprocesses:
                    if not is_proc_alive(subprocess): continue
                    subproc_key = (subprocess.pid, (" ".join(subprocess.cmdline()).strip()))
                    if len(subproc_key[1]) == 0: continue
                    if subproc_key not in self.children_info:
                        self.children_info[subproc_key] = ProcInfo()
                    subproc_mem_info = calc_proc_memory_information(subprocess)
                    if subproc_mem_info is None: continue
                    subproc_real_mem, subproc_virtual_mem = subproc_mem_info[0], subproc_mem_info[1]
                    self.children_info[subproc_key].max_real_memory = max(subproc_real_mem, self.children_info[subproc_key].max_real_memory)
                    self.children_info[subproc_key].max_virtual_memory = max(subproc_virtual_mem, self.children_info[subproc_key].max_virtual_memory)
                    total_subproc_real_mem += subproc_real_mem
                    total_subproc_virtual_mem += subproc_virtual_mem
                self.proc_info.max_real_memory = max(self.proc_info.max_real_memory, proc_real_mem + total_subproc_real_mem)
                self.proc_info.max_virtual_memory = max(self.proc_info.max_virtual_memory, proc_virtual_mem + total_subproc_virtual_mem)
            else:
                self.proc_info.max_real_memory = max(self.proc_info.max_real_memory, proc_real_mem)
                self.proc_info.max_virtual_memory = max(self.proc_info.max_virtual_memory, proc_virtual_mem)
            time.sleep(1)
