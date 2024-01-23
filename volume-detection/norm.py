import getopt
import math
import os
import re
import subprocess
import sys

# amplify
volume_amplify = 0          # passed as argument
# column tag to parse
column = "FTPK" # M         # passed as argument
# input file name
input = ""                  # passed as argument
# output file name
output = ""                 # passed as argument
# whether to show debug output
debug_mode = False          # passed as argument

# tuple_list: a 2D array of volume data, aggregated by second, each second has 10 data points.
tuple_list = []
# partition_tree: a binary tree of tuple indexes, split by peak volumes.
partition_tree = []
# volume_list: an array of quadruples, start index, end index, start volume, end volume
volume_list = []
# conversion from decibel to volume multiplier
# + 10dB = volume * 200%
# 1.0717734625362931
volume_constant = 2.0 ** 0.1
volume_modifier = 1.5       # passed as argument
max_depth = 100

############ utility functions

# time: is either momentary time (by 0.1 sec) or end time (by 1.0 sec).
# value: is either value (by 0.1 sec) or max (by 1.0 sec).
# children:
def new_tuple():
    return {"time": 0, "value": 0}

# start_region / end_region: tuple indexes that stick to the start / end of partition.
#       can overlap with parent partition's middle_tree.
#       cannot overlap with left_tree / right_tree.
# middle_tree: by defaut contains all the tuple indexes belong to this partition.
#       during split, the tuple indexes will be distributed into start_region / end_region and left_tree / right_tree.
# split_point: the peak volume that is not adjacent to either start region or end region.
#       middle_tree and split_point are represented by the same variable.
# left_tree / right_tree: point to another partition, that will do the recursive calculation.
def new_partition():
    return {"start_region": None, "left_tree": None, "middle_tree": None, "right_tree": None, "end_region": None}

def exec_shell(cmd):
    rc = os.system(cmd)
    return rc

def read_shell(cmd):
    pipe = subprocess.Popen(cmd, shell = True)
    output = pipe.stdout.read()
    return output.strip()

def regex_search(regex, input):
    output = re.search(regex, input)
    if output:
        return output.group(1)
    else:
        return ""

############ procedure functions

def get_args():
    global column
    global input
    global output
    global debug_mode
    global volume_amplify
    global volume_modifier
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:c:h:i:o:m:d", \
            ["amplify=", "column=", "help=", "input=", "output=", "modifier=", "debug"])
    except getopt.GetoptError:
        print("norm.py -i <inputfile> -o <outputfile>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("norm.py -i <inputfile> -o <outputfile>")
            sys.exit()
        elif opt in ["-a", "--amplify"]:
            volume_amplify = float(arg)
        elif opt in ["-c", "--column"]:
            column = str(arg)
        elif opt in ["-i", "--input"]:
            input = str(arg)
        elif opt in ["-o", "--output"]:
            output = str(arg)
        elif opt in ["-m", "--modifier"]:
            volume_modifier = float(arg)
        elif opt in ["-d", "--debug"]:
            debug_mode = True
    if input == "":
        sys.exit()

def parse_input():
    global column
    global input
    global tuple_list
    if debug_mode:
        print(column)
    infile = open(input, "r")
    lines = infile.readlines()
    i = 0
    max_value = -120
    max_index = -1
    children = []
    for line in lines:
        time = regex_search("t:\s*(\S+)", line)
        value = regex_search("\s" + column + ":\s*(\S+)", line)
        if time == "" or value == "":
            continue

        deci_second = new_tuple()
        deci_second["time"] = float(time)
        deci_second["value"] = float(value)
        children.append(deci_second)
        if i == 9:
            int_second = new_tuple()
            int_second["value"] = max_value
            int_second["time"] = deci_second["time"]
            int_second["max_index"] = max_index
            int_second["children"] = children
            tuple_list.append(int_second)
            max_value = -120
            children = []
            i = 0
        else:
            if deci_second["value"] > max_value:
                max_value = deci_second["value"]
                max_index = i
            i += 1
    int_second = new_tuple()
    int_second["value"] = max_value
    int_second["time"] = deci_second["time"]
    int_second["max_index"] = max_index
    int_second["children"] = children
    tuple_list.append(int_second)
    infile.close()

def init_partition():
    global partition_tree
    partition_tree = new_partition()
    partition_tree["middle_tree"] = (0, len(tuple_list) - 1)
    split_by_max(partition_tree)

def print_partition(partition, indent = 0):
    if indent == 0:
        print("============================================================")
    if partition == None:
        return
    for key in ["start_region", "left_tree", "middle_tree", "right_tree", "end_region"]:
        for i in range(0, indent):
            print(" ", end = "")
        if key in ["left_tree", "right_tree"]:
            print(key + ": ")
            print_partition(partition[key], indent + 4)
        elif key in ["middle_tree"]:
            if "middle_tree" in partition[key]:
                print(key + ": ")
                print_partition(partition[key], indent + 4)
            else:
                print(key + ": " + str(partition[key]) + " ", end = "")
                for j in range(partition[key][0], partition[key][1] + 1):
                    print(str(tuple_list[j]["value"]) + " ", end = "")
                print("")
        else:
            print(key + ": " + str(partition[key]) + " ", end = "")
            if partition[key] != None:
                # print(str(tuple_list[partition[key][0]]["value"]) + " " + str(tuple_list[partition[key][1]]["value"]))
                for j in range(partition[key][0], partition[key][1] + 1):
                    print(str(tuple_list[j]["value"]) + " ", end = "")
            print("")

def serialize_partition(partition, volume_list):
    global tuple_list
    if partition["start_region"] != None:
        start_index = partition["start_region"][0]
        end_index = partition["start_region"][1]
        volume = tuple_list[partition["start_region"][0]]["value"]
        append_volume(volume_list, start_index, end_index, volume)
    if partition["left_tree"] != None:
        serialize_partition(partition["left_tree"], volume_list)
    if partition["middle_tree"] != None:
        pass
    if partition["right_tree"] != None:
        serialize_partition(partition["right_tree"], volume_list)
    if partition["end_region"] != None:
        start_index = partition["end_region"][0]
        end_index = partition["end_region"][1]
        volume = tuple_list[partition["end_region"][1]]["value"]
        append_volume(volume_list, start_index, end_index, volume)

def append_volume(volume_list, start_index, end_index, volume):
    global tuple_list
    max_index = start_index
    if tuple_list[max_index]["value"] < tuple_list[end_index]["value"]:
        max_index = end_index
    if len(volume_list) == 0:
        volume_list.append((start_index, max_index, end_index, volume))
    else:
        last_volume = volume_list[-1]
        if volume == last_volume[3]:
            if tuple_list[max_index]["value"] < tuple_list[last_volume[0]]["value"]:
                max_index = last_volume[0]
            if tuple_list[max_index]["value"] < tuple_list[last_volume[2]]["value"]:
                max_index = last_volume[2]
            volume_list[-1] = (min(start_index, last_volume[0]), max_index, max(end_index, last_volume[2]), volume)
        else:
            volume_list.append((start_index, max_index, end_index, volume))

def convert_volume(decibel):
    return (volume_constant ** (volume_amplify - decibel)) ** volume_modifier

def print_volume(volume_list):
    global tuple_list
    if debug_mode:
        for volume in volume_list:
            print(volume)
    # for i in range(0, len(volume_list)):
    #     volume_list[i] = (volume_list[i][0], volume_list[i][1], volume_list[i][2], volume_list[i][3] ** volume_modifier)

    if debug_mode:
        print(volume_constant)
    last_volume = None
    last_time = 0
    for volume in volume_list:
        start_time = last_time
        end_time = volume[0]
        if last_time == 0:
            # static volume
            print("volume=enable='between(t,%d,%d)':volume='%.2f':eval=frame, \\" % (start_time, end_time, convert_volume(volume[-1])))
        else:
            # transition volume
            print("volume=enable='between(t,%d,%d)':volume='%.2f + (t - %d) / (%d - %d) * (%.2f - %.2f)':eval=frame, \\" % ( \
                start_time, end_time, convert_volume(last_volume[-1]), start_time, end_time, start_time, \
                convert_volume(volume[-1]), convert_volume(last_volume[-1])))
        start_time = volume[0]
        end_time = volume[2] + 1
        print("volume=enable='between(t,%d,%d)':volume='%.2f':eval=frame, \\" % (start_time, end_time, convert_volume(volume[-1])))
        last_time = volume[2] + 1
        last_volume = volume
    print("volume=enable='between(t,%d,%d)':volume='%.2f':eval=frame\\" % (last_time, math.ceil(tuple_list[-1]["time"]), convert_volume(last_volume[-1])))

############ algorithms

def get_max_index(in_tuple_list, start_index, end_index):
    local_max = -120
    out_index = -1
    for i in range(start_index, end_index + 1):
        if in_tuple_list[i]["value"] > local_max:
            local_max = in_tuple_list[i]["value"]
            out_index = i
    return out_index

def get_min_index(in_tuple_list, start_index, end_index):
    local_min = 0
    out_index = -1
    for i in range(start_index, end_index + 1):
        if in_tuple_list[i]["value"] < local_min:
            local_min = in_tuple_list[i]["value"]
            out_index = i
    return out_index

# split by max volume
def split_by_max(partition):
    global tuple_list
    start_index = partition["middle_tree"][0]
    end_index = partition["middle_tree"][1]
    split_point = -1
    while True:
        if end_index - start_index <= 3:
            # cannot split any further
            split_point = -1
            break
        else:
            split_point = get_max_index(tuple_list, start_index, end_index)
        if split_point == start_index and partition["start_region"] != None:
            partition["start_region"] = (partition["start_region"][0], split_point)
            partition["middle_tree"] = (split_point + 1, partition["middle_tree"][1])
            start_index = split_point + 1
        elif end_index == split_point and partition["end_region"] != None:
            partition["end_region"] = (split_point, partition["end_region"][1])
            partition["middle_tree"] = (partition["middle_tree"][0], split_point - 1)
            end_index = split_point - 1
        else:
            # got a valid split point
            break
    if split_point != -1:
        partition["middle_tree"] = (split_point, split_point)
        partition["left_tree"] = new_partition()
        partition["left_tree"]["middle_tree"] = (start_index, split_point - 1)
        partition["left_tree"]["start_region"] = partition["start_region"]
        partition["left_tree"]["end_region"] = partition["middle_tree"]
        partition["right_tree"] = new_partition()
        partition["right_tree"]["middle_tree"] = (split_point + 1, end_index)
        partition["right_tree"]["start_region"] = partition["middle_tree"]
        partition["right_tree"]["end_region"] = partition["end_region"]
    else:
        partition["left_tree"] = None
        partition["right_tree"] = None
    #return partition

def split_by_max_recursion(partition, level = 0):
    split_by_max(partition)
    if level == max_depth:
        return
    if partition["left_tree"] != None:
        split_by_max_recursion(partition["left_tree"], level + 1)
    if partition["right_tree"] != None:
        split_by_max_recursion(partition["right_tree"], level + 1)

def split_by_min(partition):
    pass

############

get_args()
parse_input()
init_partition()
if debug_mode:
    print(partition_tree)
    print_partition(partition_tree)
split_by_max_recursion(partition_tree["left_tree"])
split_by_max_recursion(partition_tree["right_tree"])
if debug_mode:
    print_partition(partition_tree)
serialize_partition(partition_tree, volume_list)
print_volume(volume_list)
