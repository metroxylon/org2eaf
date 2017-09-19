# Helper functions
# 1) make_ms: s.ms > ms
# 2) make_mmss:  hh.mm.ss.ms > mm.ss
import re

def make_ms(time_in):
    # test input 00:00:04.46
    if re.search("(\d\d):(\d\d):(\d\d)(\.\d+)", time_in):
        splitted = re.search("(\d\d):(\d\d):(\d\d)(\.\d+)", time_in)
        hours = int(splitted.group(1))
        minutes = int(splitted.group(2))
        seconds = int(splitted.group(3))
        mss = splitted.group(4)
        mss = float(format(float(mss), '.3f'))
        total_secs = hours * 3600 +\
                 minutes * 60 +\
                 seconds +\
                 mss
        total_ms = int(total_secs * 1000)
        return total_ms
    else:
        print("Uncommon time format: "  + time_in)
    

def make_mmss(time_in):
    splitted = re.search("(\d\d):(\d\d):(\d\d)(\.\d+)", time_in)
    minutes = splitted.group(2)
    seconds = splitted.group(3)
    time_out = minutes + ":" + seconds
    return time_out

#print(make_mmss("00:00:04.46"))
