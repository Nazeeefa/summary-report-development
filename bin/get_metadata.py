#!/usr/bin/env python
from __future__ import print_function
import xmltodict
from collections import OrderedDict
import re
import argparse
import os
import json

class RunfolderInfo():

    def __init__(self, runfolder):
        self.runfolder = runfolder
        self.run_parameters = self.read_run_parameters()
        self.stats_json = self.read_stats_json()
        self.description_and_identifier = OrderedDict()
        self.run_parameters_tags = \
            {'RunId': 'Run ID', 'RunID': 'Run ID',
             'ApplicationName': 'Control software', 'Application': 'Control software',
             'ApplicationVersion': 'Control software version',
             'Flowcell': 'Flowcell type', 'FlowCellMode': 'Flowcell type',
             'ReagentKitVersion': 'Reagent kit version',
             'RTAVersion': 'RTA Version', 'RtaVersion': 'RTA Version',
            }

    def find(self, d, tag):
        if tag in d:
            yield d[tag]
        for k, v in d.items():
            if isinstance(v, dict):
                for i in self.find(v, tag):
                    yield i

    def read_run_parameters(self):
        alt_1 = os.path.join(self.runfolder, "runParameters.xml")
        alt_2 = os.path.join(self.runfolder, "RunParameters.xml")
        if os.path.exists(alt_1):
            with open(alt_1) as f:
                return xmltodict.parse(f.read())
        elif os.path.exists(alt_2):
            with open(alt_2) as f:
                return xmltodict.parse(f.read())
        else:
            return None

    def read_stats_json(self):
        stats_json_path = os.path.join(self.runfolder, "Unaligned/Stats/Stats.json")
        if os.path.exists(stats_json_path):
            with open(stats_json_path) as f:
                return json.load(f)
        else:
            return None

    def get_bcl2fastq_version(self, runfolder):
        with open(os.path.join(runfolder, "bcl2fastq_version")) as f:
            bcl2fastq_str = f.read()
        return bcl2fastq_str.split("v")[1].strip()

    def get_run_parameters(self):
        results = OrderedDict()
        for key, value in self.run_parameters_tags.items():
            info = list(self.find(self.run_parameters, key))
            if info:
                results[value] = info[0]
        return results

    def get_read_cycles(self):
        read_and_cycles = OrderedDict()
        read_counter = 1
        index_counter = 1
        for read_info in self.stats_json["ReadInfosForLanes"][0]["ReadInfos"]:
            if read_info["IsIndexedRead"]:
                read_and_cycles[f"Index {index_counter} (bp)"] = read_info["NumCycles"]
                index_counter += 1
            else:
                read_and_cycles[f"Read {read_counter} (bp)"] = read_info["NumCycles"]
                read_counter += 1
        return read_and_cycles

    def get_info(self):
        results = self.get_read_cycles()
        results.update(self.get_run_parameters())
        if os.path.exists(os.path.join(self.runfolder, "bcl2fastq_version")):
            results['bcl2fastq version'] = self.get_bcl2fastq_version(self.runfolder)
        return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dumps a metadata yaml for MultiQC')
    parser.add_argument('--runfolder', type=str, required=True, help='Path to runfolder')

    args = parser.parse_args()
    runfolder = args.runfolder

    runfolder_info = RunfolderInfo(runfolder)
    results = runfolder_info.get_info()

    print ('''
id: 'sequencing_metadata'
section_name: 'Sequencing Metadata'
plot_type: 'html'
description: 'regarding the sequencing run'
data: |
    <dl class="dl-horizontal">
''')
    for k,v in results.items():
        print("        <dt>{}</dt><dd><samp>{}</samp></dd>".format(k,v))
    print ("    </dl>")
