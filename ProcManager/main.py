import sys
from ps_monitor import PsMonitor


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise Exception("pid is needed")
    pid = int(sys.argv[1])
    with PsMonitor(pid, True) as ps:
        print("start to monitor process %d" % pid)
        ps.run()
        print("process %d terminate" % pid)
