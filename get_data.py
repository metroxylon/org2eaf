# this module contains functions for reading the text data into python
# dictionary structure

import re
# the function make_ms in time_conversion converts hh:mm:ss.ms to miliseconds
# make_mmss converts hh:mm:ss.ms to mm:ss (used for generation of labels)
from time_conversion import make_ms, make_mmss

#-----------------------------------------------------------------------------
# Get file metadata
#-----------------------------------------------------------------------------

def make_none(string):
    if string == "" or string == "None" or string == "False" or string == "NA":
        return None
    else:
        return string

def get_file_metadata(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        filelines = f.readlines()
    file_metadata = {}
    for line in filelines[:20]:
        if re.search(":AUDIO:", line):
            file_metadata["audiofile"] = make_none(line.replace(":AUDIO:", "").strip())
        elif re.search(":VIDEO:", line):
            file_metadata["videofile"] = make_none(line.replace(":VIDEO:", "").strip())
    if len(file_metadata) == 0:
        print("File has no metadata!")
    return file_metadata

#-----------------------------------------------------------------------------
#Check data completeness
#-----------------------------------------------------------------------------

def check_data_completeness(text_unit, text_units={}):
    # unit dictionary
    text = text_unit["data"]["tx"]
    if "label" not in text_unit["meta"]:
        print("No label for: " + text)
        print("This will result in a mess. Fix immediately!")
        label = "NA"
    else:
        label = text_unit["meta"]["label"]
    if label in text_units:
        print("Duplicate label " + label)
    if "speaker" not in text_unit["meta"]:
        print("No speaker in: " + label)
        print("------------")
    elif text_unit["meta"]["speaker"].strip() == "":
        print("Empty speaker in " + label)
    if "time1" not in text_unit["meta"]:
        print("Time missing in " + label)

# Test suit
test1 = [{"meta" : {"label" : "SOME00:12"}, "data" : {"tx" : "bla bla bla"}}, {"SOME00:12", "SOME00:23"}]

test2 = [{"meta" : {}, "data" : {"tx" : "bla bla bla"}}, {"SOME00:23"}]

tests = [test1, test2]

# for test in tests:
#     check_data_completeness(test[0], test[1])

#-----------------------------------------------------------------------------
# get data from file
# to read into following dictionary structure
# LABEL = {meta : {time1 : xxx,
#                  time2 : yyy,
#                  speaker : someone,
#                  label : something,
#                  disslabel : something else,
#                  comment : some,
#                  media : some file},
#          data : {tx : some text,
#                  mb : some morphemes,
#                  gl : some glosses,
#                  ft : some translation,
#                  keys : dictionary keys}
#                  }
#-----------------------------------------------------------------------------

def get_data(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        filelines = f.readlines()
    story_units = {}
    ordered_ids = []
    new_unit = {"meta" : {}, "data" : {}}
    dissstory_key = None
    for line in filelines:
        if re.search("##BEGIN##", line):
            dissstory_key = line.replace("##BEGIN##", "").strip()
        elif re.search("##END##", line):
            dissstory_key = None
        elif line[0:3] == "** ":
            tx = line.replace("**", "")
            tx = tx.replace("DONE", "")
            tx = tx.replace("TODO", "").strip()
            new_unit["data"]["tx"] = tx
        elif re.search("\[MB\]", line):
            new_unit["data"]["mb"] = line.replace("[MB]", "").strip()
        elif re.search("\[GL\]", line):
            new_unit["data"]["gl"] = line.replace("[GL]", "").strip()
        elif re.search("\[FT\]", line):
            new_unit["data"]["ft"] = line.replace("[FT]", "").strip()
        elif re.search("\[RC\]", line):
            media = re.sub(".+\/([^\/]+)::.+", "\g<1>", line)
            new_unit["meta"]["media"] = media
        elif re.search(":KEYS:", line):
            keys = line.replace(":KEYS:", "").strip()
            new_unit["data"]["keys"] = keys
        elif re.search(":SPEAKER:", line):
            speaker = line.replace(":SPEAKER:", "").strip()
            new_unit["meta"]["speaker"] = speaker
        elif re.search(":LABEL:", line):
            label = line.replace(":LABEL:", "").strip()
            label = label.replace("<", "")
            label = label.replace(">", "")
            new_unit["meta"]["label"] = label
        elif re.search(":TC:", line):
            tc = line.replace(":TC:", "").strip()
            if tc != "":
                tc = tc.split("-")
                time1 = make_ms(tc[0].strip())
                time2 = make_ms(tc[1].strip())
                if dissstory_key != None:
                    disslab = dissstory_key + make_mmss(tc[0].strip())
                else:
                    disslab = "-"
                new_unit["meta"]["time1"] = time1
                new_unit["meta"]["time2"] = time2
                new_unit["meta"]["disslabel"] = disslab
            else:
                print("Missing time in: " + label)
        elif re.search(":COM:", line):
            comment = line.replace(":COM:", "").strip()
            new_unit["meta"]["comment"] = comment
        # elif re.search(":PIC:", line):
        #     pic = line.replace(":PIC:", "").strip()
        #     new_unit["meta"]["comment"] = new_unit["meta"]["comment"] + pic
        elif line.strip() == ":END:":
            if len(new_unit["data"]) != 0:
                check_data_completeness(new_unit)
                story_units[label] = new_unit
                ordered_ids.append(label)
            new_unit = {"meta" : {}, "data" : {"keys" : ""}}
    return story_units, ordered_ids


        


