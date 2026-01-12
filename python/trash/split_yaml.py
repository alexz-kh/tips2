#!/usr/bin/env python3
"""
Split a multi-document YAML file into separate files named <uuid>.yaml.

Usage:
  python split_yaml_uuid.py input.yaml [-o OUTDIR] [--log-level INFO]

Each non-empty document is written to:
  <OUTDIR or <input_dir>/<input_stem>_parts>/<random-uuid>.yaml
"""

# from __future__ import annotations
import argparse
import logging as log
import os.path
from os import mkdir
from pathlib import Path
from collections import OrderedDict
import uuid

import yaml


def setup_logging(level: str = "INFO") -> None:
    log.basicConfig(
        level=getattr(log, level.upper(), log.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )


##
def ordered_dict_representer(self, value):
    return self.represent_mapping('tag:yaml.org,2002:map', value.items())


# Always single-quote strings
def _repr_str(dumper, value: str):
    return dumper.represent_scalar('tag:yaml.org,2002:str', value, style="'")


# Render ints/floats as *strings* (quoted)
def _repr_int(dumper, value: int):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(value), style="'")


def _repr_float(dumper, value: float):
    # str(value) yields 'nan', 'inf', '-inf' as text; we keep them as strings
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(value), style="'")


yaml.add_representer(str, _repr_str)
yaml.add_representer(int, _repr_int)  # bool has its own representer, so it's safe
yaml.add_representer(float, _repr_float)
yaml.add_representer(OrderedDict, ordered_dict_representer)


##


def main() -> int:
    ap = argparse.ArgumentParser(description="Split multi-doc YAML into <uuid>.yaml files.")
    ap.add_argument("input", help="Path to input YAML with '---' separators")
    ap.add_argument("-o", "--out-dir",
                    help="Output directory (default: <input_dir>/<input_stem>_parts/)")
    ap.add_argument("--log-level", default="INFO",
                    help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    args = ap.parse_args()

    setup_logging(args.log_level)

    in_path = Path(args.input)
    if not in_path.is_file():
        log.error("Input file not found: %s", in_path)
        return 1

    out_dir = Path(args.out_dir) if args.out_dir else (in_path.parent / f"{in_path.stem}_parts")
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info("Output directory: %s", out_dir)

    count_total = 0
    count_written = 0
    list_names = []
    list_objs = []
    from collections import defaultdict
    result = defaultdict()
    print_result = list()

    try:
        with in_path.open("r", encoding="utf-8") as f:
            for idx, doc in enumerate(yaml.safe_load_all(f), start=1):
                count_total += 1
                if doc is None:
                    log.debug("Skipping empty document at index %d", idx)
                    continue
                doc['metadata']['namespace'] = '{{ target_namespace }}'
                if doc['metadata'].get('labels', {}).get('cluster.sigs.k8s.io/cluster-name', ''):
                    doc['metadata']['labels']['cluster.sigs.k8s.io/cluster-name'] = '{{ target_cluster }}'
                if doc['kind'] == 'BareMetalHostCredential':
                    doc['spec']['password']['value'] = 'r00tme'
                    # print('  - {{- render(\'baremetalhostcredentials.kaas.mirantis.com/' + _fname + '\', indent=4) }}')
                # if doc['kind'] == 'BareMetalHostInventory':
                #     print('  - {{- render(\'baremetalhostinventories.kaas.mirantis.com/' + _fname + '\', indent=4) }}')
                list_objs.append(doc)

                # count_written += 1
                # log.info("Wrote %s (doc #%d)", out_file, idx)
        for doc in list_objs:
            nodename = f'{doc['metadata']['name'].split('vm')[0]}'
            if not result.get(nodename, []):
                result[nodename] = []
            result[nodename].append(doc)
        for k in result.keys():
            out_com_file = os.path.join(str(out_dir), "virts.yaml.j2")
            out_f_dir = os.path.join(str(out_dir), f"kvm-{k}")
            if not os.path.isdir(out_f_dir):
                mkdir(out_f_dir)

            for doc in result[k]:
                _f_name = f'{doc['metadata']['name']}.yaml.j2'
                obj_name = doc['metadata']['name']
                out_file = os.path.join(str(out_f_dir), _f_name)
                if [i[0]['kind'] for i in result.values()][0] == 'BareMetalHostCredential':
                    # print_result.append(obj_name)
                    print("  {'name': '" + obj_name + "'},")
                if [i[0]['kind'] for i in result.values()][0] == 'BareMetalHostInventory':
                    # print_result.append(obj_name)
                    _mac = doc['spec']['bootMACAddress']
                    _address = doc['spec']['bmc']['address']
                    print("  {{'name': '{0}', 'mac': '{1}', 'ipmi': '{2}' }},".format(obj_name, _mac, _address))
                if [i[0]['kind'] for i in result.values()][0] == 'Machine':
                    _bmh_id = doc['metadata']['name'].split('-')[0]
                    _rack_id = [i['value'] for i in doc['spec']['providerSpec']['value']['nodeLabels'] if i['key'] == 'rack-id'][0]
                    print("  {{'name': '{0}', 'bmh_id': '{1}', 'rack_id': '{2}' }},".format(obj_name, _bmh_id, _rack_id))

                # if [i[0]['kind'] for i in result.values()][0] == 'BareMetalHostInventory':
                #     _text = '  - {{- render(\'baremetalhostinventories.kaas.mirantis.com/' + f"kvm-{k}" + '/' + _f_name + '\', indent=4) }}'
                #     #print(_text)
                #     with open(out_com_file, 'a', encoding="utf-8") as save_f:
                #         save_f.write(_text + '\n')
                # if [i[0]['kind'] for i in result.values()][0] == 'BareMetalHostCredential':
                #     _text = '  - {{- render(\'baremetalhostcredentials.kaas.mirantis.com/' + f"kvm-{k}" + '/' + _f_name + '\', indent=4) }}'
                #     #print(_text)
                #     with open(out_com_file, 'a', encoding="utf-8") as save_f:
                #         save_f.write(_text + '\n')
                # if [i[0]['kind'] for i in result.values()][0] == 'Machine':
                #     _text = '  - {{- render(\'machines/' + f"kvm-{k}" + '/' + _f_name + '\', indent=4) }}'
                #     #print(_text)
                #     with open(out_com_file, 'a', encoding="utf-8") as save_f:
                #         save_f.write(_text + '\n')
                #
                # with open(out_file, 'w', encoding="utf-8") as save_f:
                #     yaml.dump(doc, save_f,
                #                   sort_keys=False,
                #                   explicit_start=False,
                #                   default_flow_style=False, indent=2)

    except yaml.YAMLError as e:
        log.error("YAML parse error in %s: %s", in_path, e)
        raise Exception()
    except Exception as e:
        log.error("Failed: %s", e)
        raise Exception()
    log.info("Done. Documents seen: %d, written: %d", count_total, count_written)


if __name__ == "__main__":
    main()
