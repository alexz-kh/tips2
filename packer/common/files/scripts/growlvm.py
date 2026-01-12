#!/usr/bin/env python
#
# Copyright 2018 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


"""Growpart python module

The module is aimed to extend logical volumes according to sizes provided
in image layout.

Example:
  python growlvm --image-layout-file '/root/mylayout.yml'

Attributes:
  image-layout - json string with image layout. Supported params and
                 description might be found in IMAGE_LAYOUT_SCHEMA

"""

__version__ = '1.0'

import argparse
import collections
import yaml
from jsonschema import validate
import logging
import os
import re
import subprocess
import sys


LOG = logging.getLogger(__name__)

DECIMAL_REG = re.compile(r"(\d+)")

IMAGE_LAYOUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Image partition layout",
    "type": "object",
    "patternProperties": {
        ".*": {"$ref": "#/definitions/logical_volume_layout"}
    },
    "definitions": {
        "logical_volume_layout": {
            "type": "object",
            "properties": {
                "name": {
                    "description": "Logical Volume Name",
                    "type": "string"
                },
                "size": {
                    "description": (
                        "Size of Logical volume in units of logical extents. "
                        "The number might be volume size in units of "
                        "megabytes. A size suffix of M for megabytes, G for "
                        "gigabytes, T for terabytes, P for petabytes or E for "
                        "exabytes is optional. The number can also be "
                        "expressed as a percentage of the total space in the "
                        "Volume Group with the suffix %VG. Percentage of the "
                        "changeble values like free space is not supported."
                        ),
                },
                "resizefs": {
                    "description": (
                        "Resize underlying filesystem together with the "
                        "logical volume using fsadm(8)."
                    ),
                    "type": "boolean"
                },
                "vg": {
                    "description": ("Volume group name to resize logical "
                                    "volume on."),
                    "type": "string"
                }
            },
            "additionalProperties": False,
            "required": ["size"]
        }
    },
}


def get_volume_groups_info(unit, vg):
    cmd = ("vgs --noheadings -o vg_name,size,free,vg_extent_size --units %s "
           "--separator ';' %s") % (unit, vg)
    try:
        output = subprocess.check_output(cmd, shell=True,
                                         stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Exception("Failed to get volume group info", exc.output)

    vgs = []
    for line in output.splitlines():
        parts = line.strip().split(';')
        vgs.append({
            'name': parts[0],
            'size': int(DECIMAL_REG.match(parts[1]).group(1)),
            'free': int(DECIMAL_REG.match(parts[2]).group(1)),
            'ext_size': int(DECIMAL_REG.match(parts[3]).group(1))
        })
    return vgs


def get_logical_volume_info(unit, vg):
    cmd = ("lvs -a --noheadings --nosuffix -o lv_name,size,lv_attr --units %s "
           "--separator ';' %s") % (unit, vg)
    try:
        output = subprocess.check_output(cmd, shell=True,
                                         stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Exception("Failed to get volume info", exc.output)

    lvs = []

    for line in output.splitlines():
        parts = line.strip().split(';')
        lvs.append({
            'name': parts[0].replace('[', '').replace(']', ''),
            'size': int(DECIMAL_REG.match(parts[1]).group(1)),
        })
    return lvs


def normalize_to_pe(size, pe):
    """ Make sure requested size is multiply of PE

    PE is gathered from system with honor of provided units,
    when volume size is set in Gigabytes, PE (4mb default) will
    be shown as 0.
    """

    if pe > 0:
        return (size // pe + 1) * pe

    return size


def main():
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    LOG.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(
        description=('Grow lvm partitions and theirs filesystems to '
                     'specified sizes.')
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--image-layout',
        help='json based image layout',
    )
    group.add_argument(
        '--image-layout-file',
        help='Path to file with image layout',
    )
    args = parser.parse_args()

    if args.image_layout_file:
        with open(args.image_layout_file) as f:
            layout_info = yaml.load(f)
    else:
        layout_info = yaml.load(args.image_layout)

    LOG.info("Validating provided layout.")
    try:
        validate(layout_info, IMAGE_LAYOUT_SCHEMA)
    except Exception as e:
        LOG.error("Validation of provided layout failed.")
        raise e

    for part_name, part_layout in layout_info.iteritems():

        size_opt = '--size'
        size_unit = 'm'

        size = part_layout['size']
        vg = part_layout.get('vg', 'vg0')
        resizefs = part_layout.get('resizefs', True)

        if size:
            if '+' in size:
                raise Exception("Setting relative size is not supported.")
            # LVCREATE(8) -l --extents option with percentage
            elif '%' in size:
                size_parts = size.split('%', 1)
                size_percent = int(size_parts[0])
                if size_percent > 100:
                    raise Exception(
                        "Size percentage cannot be larger than 100%")
                size_whole = size_parts[1]
                if size_whole == 'ORIGIN':
                    raise Exception("Snapshot Volumes are not supported")
                elif size_whole not in ['VG']:
                    raise Exception("Relative sizes are not supported.")
                size_opt = '--extents'
                size_unit = ''
            else:
                # LVCREATE(8) -L --size option unit
                if size[-1].lower() in 'bskmgtpe':
                    size_unit = size[-1].lower()
                    size = size[0:-1]

        # when no unit, megabytes by default
        if size_opt == '--extents':
            unit = 'm'
        else:
            unit = size_unit

        vgs = get_volume_groups_info(unit, vg)
        this_volume_group = vgs[0]
        pe = this_volume_group['ext_size']

        lvs = get_logical_volume_info(unit, vg)

        LOG.info("Volume group info: %s", vgs)
        LOG.info("Logical Volume info: %s", lvs)

        this_volume = [v for v in lvs if v['name'] == part_name][0]

        LOG.info("Using %s for volume: %s", size_opt, this_volume)
        if size_opt == '--extents':
            size_free = this_volume_group['free']
            if size_whole == 'VG':
                size_requested = normalize_to_pe(
                    size_percent * this_volume_group['size'] / 100, pe)

            LOG.info("Request %s size for volume %s",
                     size_requested, this_volume)
            if this_volume['size'] > size_requested:
                raise Exception("Redusing volume size in not supported.")
            elif this_volume['size'] < size_requested:
                if (size_free > 0) and (('+' not in size) or
                   (size_free >= (size_requested - this_volume['size']))):
                    cmd = "lvextend "
                else:
                    raise Exception(
                        ("Logical Volume %s could not be extended. Not "
                         "enough free space left (%s%s required / %s%s "
                         "available)"),
                        this_volume['name'],
                        size_requested - this_volume['size'],
                        unit, size_free, unit
                    )
                if resizefs:
                    cmd += "--resizefs "

                cmd = "%s -%s %s%s %s/%s" % (
                    cmd, size_opt, size, size_unit, vg, this_volume['name'])
                try:
                    LOG.debug("Executing command: %s", cmd)
                    output = subprocess.check_output(
                        cmd,
                        shell=True,
                        stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as exc:
                    raise Exception(
                        "Failed to resize volume %s. Exception: %s" % (
                            part_name, exc.output))
            else:
                LOG.info("No need to resize volume %s.", part_name)
        else:
            cmd = "lvresize "
            if normalize_to_pe(int(size), pe) > this_volume['size']:
                if resizefs:
                    cmd += "--resizefs "
                cmd = "%s -%s %s%s %s/%s" % (
                    cmd, size_opt, size, size_unit, vg, this_volume['name'])
                try:
                    LOG.debug("Executing command: %s", cmd)
                    output = subprocess.check_output(
                        cmd,
                        shell=True,
                        stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as exc:
                    raise Exception(
                        "Failed to resize volume %s. Exception: %s" % (
                            part_name, exc.output))

            elif normalize_to_pe(int(size), pe) == this_volume['size']:
                LOG.info("No need to resize volume %s.", part_name)
            else:
                raise Exception(
                    "Redusing size in not supported for provided layout.")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        LOG.exception("Failed to apply image layout: %s", e)
        sys.exit(1)
