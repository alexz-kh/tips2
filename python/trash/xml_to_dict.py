#!/usr/bin/env python3
"""
List NIC MAC addresses from libvirt domain XMLs.
python3 ./xml_to_dict.py -d /etc/libvirt/qemu

Default dir: /etc/libvirt/qemu
"""

import argparse
import logging as log
import secrets
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

import yaml

logger = log.getLogger(__name__)


def iter_nics_from_root(root):
    """
    Yield dicts with NIC info from a parsed libvirt domain XML root.
    Looks under ./devices/interface/* and returns entries with a <mac address=...>.
    """
    devices = root.find("devices")
    if devices is None:
        return
    for iface in devices.findall("interface"):
        mac_el = iface.find("mac")
        if mac_el is None:
            continue
        mac = (mac_el.get("address") or "").strip()
        if not mac:
            continue

        target_el = iface.find("target")
        model_el = iface.find("model")
        source_el = iface.find("source")
        alias_el = iface.find("alias")
        #    <interface type='bridge'>
        #      {% set n = (node.nics | selectattr('name','equalto', 'nic2') | list | first)   %}
        #      <mac address='{{ n.mac }}'/>
        #      <source bridge='br-k8s-pods'/>
        #      <model type='virtio'/>
        #      <address type='pci' domain='0x0000' bus='0x03' slot='0x00' function='0x0'/>
        #    </interface>

        yield {
            "mac": mac,
            "target_dev": target_el.get("dev") if target_el is not None else None,
            "model": model_el.get("type") if model_el is not None else None,
            "source": source_el.get("bridge") if model_el is not None else None,
            "alias": alias_el.get("name") if alias_el is not None else None,
        }


def extract_domain_name(root, fallback):
    name_el = root.find("name")
    if name_el is not None and name_el.text:
        return name_el.text.strip()
    return fallback


def scan_dir(dir_path: Path):
    nodes = []
    for xml_path in sorted(dir_path.glob("*.xml"), key=lambda p: p.name):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.warning("Failed to parse %s: %s", xml_path, e)
            continue

        domain = extract_domain_name(root, xml_path.stem)
        CHARS = "0123456789abcdef"
        LENGTH = 8

        nodes.append(OrderedDict({
            'name': domain,
            'memory_gib': 52,
            'vcpu': 8,
            'uefi': True,
            'disks': [
                OrderedDict({'name': 'disk0',
                             'dev': 'sda',
                             'size': '120G',
                             'format': 'raw',
                             'serial_number': ''.join(secrets.choice(CHARS) for _ in range(LENGTH)).upper()
                             }), ],
            'nics': [
                {'mac': [nic['mac'] for nic in iter_nics_from_root(root) if nic['source'] == 'br-pxe'][0],
                 'name': 'nic0'},
                {'mac': [nic['mac'] for nic in iter_nics_from_root(root) if nic['source'] == 'br-k8s-lcm'][0],
                 'name': 'nic1'},
                {'mac': [nic['mac'] for nic in iter_nics_from_root(root) if nic['source'] == 'br-k8s-pods'][0],
                 'name': 'nic2'},
                {'mac': [nic['mac'] for nic in iter_nics_from_root(root) if nic['source'] == 'br-ceph-p'][0],
                 'name': 'nic3'},
                {'mac': [nic['mac'] for nic in iter_nics_from_root(root) if nic['source'] == 'br-tenant'][0],
                 'name': 'nic4'},
                {'mac': [nic['mac'] for nic in iter_nics_from_root(root) if nic['source'] == 'br-migrate'][0],
                 'name': 'nic5'},
                {'mac': [nic['mac'] for nic in iter_nics_from_root(root) if nic['source'] == 'br-floating'][0],
                 'name': 'nic6'},
            ]
        }))

    def ordered_dict_representer(self, value):
        return self.represent_mapping('tag:yaml.org,2002:map', value.items())

    # Always single-quote strings
    def _repr_str(dumper, value: str):
        return dumper.represent_scalar('tag:yaml.org,2002:str', value, style="'")
    yaml.add_representer(str, _repr_str)

    # Render ints/floats as *strings* (quoted)
    def _repr_int(dumper, value: int):
        return dumper.represent_scalar('tag:yaml.org,2002:str', str(value), style="'")

    def _repr_float(dumper, value: float):
        # str(value) yields 'nan', 'inf', '-inf' as text; we keep them as strings
        return dumper.represent_scalar('tag:yaml.org,2002:str', str(value), style="'")

    yaml.add_representer(int, _repr_int)  # bool has its own representer, so it's safe
    yaml.add_representer(float, _repr_float)

    yaml.add_representer(OrderedDict, ordered_dict_representer)
    print(yaml.dump(nodes, default_flow_style=False))


def main():
    ap = argparse.ArgumentParser(description="Print NIC MACs from libvirt domain XMLs.")
    ap.add_argument("-d", "--dir", default="/etc/libvirt/qemu", help="Directory with domain XMLs")
    ap.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, ...)")
    args = ap.parse_args()

    log.basicConfig(level=getattr(log, args.log_level.upper(), log.INFO),
                    format="%(asctime)s %(levelname)s %(message)s")

    dir_path = Path(args.dir)
    if not dir_path.is_dir():
        logger.error("Not a directory: %s", dir_path)
        return 1

    scan_dir(dir_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
