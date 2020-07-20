#
# OtterTune - LatencyUDF.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#

import sys
import json
from collections import OrderedDict
import subprocess
import logging
LATENCY_99TH = '99th_lat_ms'
LOG = logging.getLogger()
# LOG.setLevel(logging.DEBUG)
LOG.setLevel(logging.INFO)


def main():
    if (len(sys.argv) != 3):
        raise Exception(
            "Usage: python udf.py [Output Directory] [Oltpbench result Directory]"
        )
    RESULT_DIR = sys.argv[2]
    OUTPUT_DIR = sys.argv[1]
    if 'sysbench.log' in RESULT_DIR:
        s_cmd1 = "cat {} | grep '99th' | ".format(RESULT_DIR)
        s_cmd2 = " awk '{print $3}' "
        s_cmd = s_cmd1 + s_cmd2
        LOG.info(s_cmd)
        lat_status, lat_99th = subprocess.getstatusoutput(s_cmd)
        print(lat_99th)
    else:
        cmd_1 = "cd {} && ls -lrth {}/ | grep res| tail -n 1 | ".format(
            RESULT_DIR, RESULT_DIR)
        cmd_2 = " awk '{print $9}' | xargs cat | awk -F ',' '{print $10}'| tail -n 1"
        lat_cmd = cmd_1 + cmd_2
        LOG.info(lat_cmd)
        # e_cmd = "cd {}/ && ls -lrth {}/ | grep res| tail -n 1 | awk '{print $9}' | xargs cat | awk -F ',' '{print $10}'| tail -n 1".format(
        #     RESULT_DIR, RESULT_DIR)
        # print("e_cmd="+e_cmd)
        lat_status, lat_99th = subprocess.getstatusoutput(lat_cmd)
        # lat_status,  lat_99th = subprocess.getstatusoutput(e_cmd)
    LOG.info(str(lat_status) + str(lat_99th))
    if lat_status != 0:
        LOG.error("get 99th latency result path failed ")
        exit()

    # part2 add lat_99th to summary file
    sum_cmd_1 = "ls -lrth {}/ | grep summary | tail -n 1 ".format(OUTPUT_DIR)
    sum_cmd_2 = "| awk '{print $9}' "
    sum_cmd = sum_cmd_1 + sum_cmd_2
    summary_status, summary_filename = subprocess.getstatusoutput(sum_cmd)
    # summary_status, summary_filename = subprocess.getstatusoutput(
    #     "ls -lrth {}/ | grep summary | tail -n 1 | awk '{print $9}' ".format(OUTPUT_DIR))
    LOG.info(str(summary_status) + summary_filename)
    if summary_status != 0:
        LOG.error("get summary filename failed")
        exit()
    print(sys.argv[1] + "/" + summary_filename)
    conf = None
    with open(sys.argv[1] + "/" + summary_filename, "r+") as f:
        conf = json.load(f, encoding="UTF-8", object_pairs_hook=OrderedDict)
        conf[LATENCY_99TH] = lat_99th
    with open(sys.argv[1] + "/" + summary_filename, "w+") as fw:
        fw.write(json.dumps(conf, indent=4))


if __name__ == "__main__":
    main()
