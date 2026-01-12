#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import copy
import pprint as pprint
import logging as LOG

import tempfile
from shutil import copyfile

import lib as ut

LOG.basicConfig(level=LOG.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                format='%(asctime)-15s - [%(levelname)s] %(module)s:%(lineno)d: '
                       '%(message)s', )

cfgFile = os.environ.get("CONFIG_FILE", "config_infra.yaml")
SAVE_YAML = ut.str2bool(os.environ.get("SAVE_YAML", False))
GERRIT_CACHE = ut.str2bool((os.environ.get("GERRIT_CACHE", False)))

try:
    import ipdb
except ImportError:
    print("no ipdb")


def get_current_list(cfg):
    """
    Took all from gerrit-ls
    and parse with target rules
    Return all project for all targets

    """
    NewGitrepoYamlMask = os.path.join(cfg.get('drop', 'w1'),
                                      cfg.get('new_gitrepoCfgFileMask',
                                              'gitrepoCfgFile'))
    OldGitrepoCfgFile = cfg.get(
        "old_gitrepoCfgFileMask", "old_gitrepoCfgFileMask")

    current_proj_list = {}
    for t in cfg['targets']:
        new_gitrepo_cfg = []
        reportDump = []
        dst_root = cfg['targets'][t].get('dst_root', None)
        dump_to_file = NewGitrepoYamlMask + '_' + t + '.yaml'
        reportFile = dump_to_file.replace(os.path.basename(dump_to_file),
                                          "report_" + os.path.basename(
                                              dump_to_file))
        oldGitrepoCfgFile = OldGitrepoCfgFile + '_' + t + '.yaml'
        current_proj_list[t] = get_current_one_target(cfg['targets'][t],cfg=cfg)
    return current_proj_list


def get_current_one_target(_target,cfg=None):
    g_target = copy.deepcopy(_target)
    g_prefixes = g_target.get('prefixes', [])
    target_branches = g_target.get('branches_all', [])
    # Some projects have more then one branch for process.
    extra_branches = g_target.get('project_custom_branches', {}).values()
    resulted_dict = {}

    def _get_list(g_branches, _prefix):
        """
        Gerrit ls-project don't support multiple prefixes :(
        At least, our version.
        :param g_branches:
        :param _prefix:
        :return:
        """
        gerrit_host = cfg['gerrit_host']
        fd, t_path = tempfile.mkstemp()
        branches_string = ""
        clean_result = {}
        for branch in g_branches:
            branches_string += " --show-branch {}".format(branch)
        try:
            with os.fdopen(fd, 'w') as tmp:
                LOG.debug("Attemp to get project list from gerrit...")
                ut.execute(
                    'ssh -p 29418', gerrit_host, 'gerrit',
                    'ls-projects', branches_string, '--format json', '--prefix',
                    _prefix, '--type CODE',
                    check_exit_code=[0], logged=False,
                    to_filename=t_path)
                result = ut.read_yaml(t_path)
                # Drop unneded info from gerrit
                for k in result.keys():
                    if k in clean_result:
                        LOG.eror("Duplicate detected:{}".format(k))
                    clean_result[k] = {'branches': result[k]['branches']}
                return clean_result
        finally:
            os.remove(t_path)

    # FIXME somehow make it pretty...
    # Have no idea how its work, some old black-magic.
    if extra_branches:
        extra_branches.sort()
        extra_branches = list(
            b_list for b_list, _ in itertools.groupby(extra_branches))
        for _tBranch in list(itertools.chain(*extra_branches)):
            if _tBranch not in target_branches:
                target_branches.append(_tBranch)
    for g_prefix in g_prefixes:
        resulted_dict.update(_get_list(target_branches, g_prefix))
    return resulted_dict


def parse_list(list_file):
    """
    Those fun parse unpacked Packages.gz text file
    Return per package structure!
    """
    pkgs = {}
    l1 = ut.read_file(list_file)

    def process_one(l_start, l_end):
        priv_spec = 'err'
        priv_code = 'err'
        name = 'err'
        version = 'err'
        source = False
        shift = 0
        # catch whole pkg data, whole - till next empty line..
        for p in range(l_start, l_end):
            # stop on new section
            if l1[p] in ['\n', '\r\n', '']:
                shift = p
                break
            else:
                if l1[p].startswith('Package:'):
                    name = l1[p].split('Package:')[1].replace(
                        ' ', '').replace('\n', '')
                elif l1[p].startswith('Private-Mcp-Code-Sha:'):
                    priv_code = l1[p].split(
                        'Private-Mcp-Code-Sha:')[1].replace(' ', '').replace(
                        '\n', '')
                elif l1[p].startswith('Private-Mcp-Spec-Sha:'):
                    priv_spec = l1[p].split(
                        'Private-Mcp-Spec-Sha:')[1].replace(' ', '').replace(
                        '\n', '')
                elif l1[p].startswith('Source:'):
                    source = l1[p].split('Source:')[1].replace(
                        ' ', '').replace('\n', '')
                elif l1[p].startswith('Version:'):
                    version = l1[p].split('Version:')[1].replace(
                        ' ', '').replace('\n', '')
        #if not source:
        #    LOG.warning("Pkg don't have source definition:{}".format(name))
        pkg = {'Private-Mcp-Spec-Sha': priv_spec,
               'Private-Mcp-Code-Sha': priv_code,
               'source': source or name,
               'name': name,
               'version': [version]}
        return pkg, shift

    shift = 0
    i = 0
    #LOG.debug("Len:{}".format(len(l1)))
    while i in range(len(l1) -1 ):
        #LOG.debug("iter={}, shift{}".format(i,shift))
        if l1[i] in ['\n', '\r\n', ''] or i in range(shift) and not 0:
            #      print("Skip: empty")
            i = shift + 1
            continue
        try:
            #LOG.debug("Catch : iter={}, shift{}".format(i,shift))
            rez, shift = process_one(i, len(l1))
            if rez['name'] in pkgs.keys():
                # TODO , catch sha's and etc for duplicates
                LOG.warning('Duplicate pkgs:{}'.format(rez['name']))
                pkgs[rez['name']]['version'] = pkgs[rez['name']]['version'] + \
                                               rez['version']
            else:
                pkgs[rez['name']] = rez
            i = shift + 1
        except Exception as e:
            LOG.error("Error parse packages section")
            sys.exit(1)
    return pkgs


def check_deb_in_git(git_list):
    """
    Check that deb exist in git's. KISS
    Whole structure hardcoded for `openstack` and `specs`
    """
    _specs = []
    for k in git_list['specs'].keys(): _specs.append(k.split('/')[-1])
    _openstack = []
    for k in git_list['openstack'].keys(): _openstack.append(k.split('/')[-1])
    # _src = []
    # for p in deb_pkgs.keys(): _src.append((deb_pkgs[p]['source']))
    # _uniq_src = set(_src)
    #
    _n_src = {}
    # uniq list by deb source
    for p in deb_pkgs.keys():
        _n_src[deb_pkgs[p]['source']] = {
            'Private-Mcp-Code-Sha': deb_pkgs[p]['Private-Mcp-Code-Sha'],
            'Private-Mcp-Spec-Sha': deb_pkgs[p]['Private-Mcp-Spec-Sha']
        }
    _pkgs_no_spec = []
    _pkgs_no_src = []
    _pkgs_with_spec = []
    _pkgs_with_src = []
    _pkgs_nice = {}
    # FIXME hardcoode
    _black_spec = cfg['targets']['specs'].get('project_blacklist', [])
    _black_src = cfg['targets']['openstack'].get('project_blacklist', [])
    _git_src_prefix = cfg['targets']['openstack'].get('prefixes', [])[0]
    _git_spec_prefix = cfg['targets']['specs'].get('prefixes', [])[0]
    if len(cfg['targets']['openstack'].get('prefixes', [])) > 1 or len(cfg['targets']['specs'].get('prefixes', [])) > 1:
        LOG.error("I cant work with multiply prefixes ;(")
        sys.exit(1)
    for p in _n_src.keys():
        # Check that related deb pkg 'source:' in git specs
        if p in _black_spec and p in _specs:
            LOG.info("Blacklisted from specs:{}".format(p))
        elif p not in _specs:
            LOG.error("Not in specs:{}".format(p))
            _pkgs_no_spec.append(p)
        else:
            _pkgs_with_spec.append(p)
            # God bless that source: == last part of string!
            _specs_path = [k for k in git_list['specs'] if k.endswith(p)]
            _branches = list(
                git_list['specs'][os.path.join(_git_spec_prefix, p)][
                    'branches'].keys())
            if len(_specs_path) > 1:
                LOG.warning("Fix duplicate SPECS PATH manually:{}".format(_specs_path))
            _pkgs_nice[p] = {
                'specs': {
                    'path': _specs_path,
                    'Private-Mcp-Spec-Sha': _n_src[p]['Private-Mcp-Spec-Sha'],
                    'branches': _branches}}
        # Check that related deb pkg 'source:' in git sources
        if p in _black_src and p in _openstack:
            LOG.info("Blacklisted from sources:{}".format(p))
        if p not in _openstack:
            LOG.warning("Not in soures:{}".format(p))
            _pkgs_no_src.append(p)
        else:
            # God bless that source: == last part of string!
            _pkgs_with_src.append(p)
            # If pkgs missed from specs - it would fail to add source key
            if not _pkgs_nice.get(p, False):
                _pkgs_nice[p] = {}
            # FIXME check for overwrite!
            _pkgs_nice[p]['source'] = [k for k in git_list['openstack'] if
                                       k.endswith(p)]
            # Check for not work k.endswith magic
            _src_path = [k for k in git_list['openstack'] if k.endswith(p)]
            _branches = list(
                git_list['openstack'][os.path.join(_git_src_prefix, p)][
                    'branches'].keys())
            if len(_src_path) > 1:
                LOG.warning("Fix duplicate SOURCE PATH manually:{}".format(_src_path))
            _pkgs_nice[p]['source'] = {
                'path': _src_path,
                'Private-Mcp-Code-Sha': _n_src[p]['Private-Mcp-Code-Sha'],
                'branches': _branches}

    rez = {'pkgs_no_src': sorted(_pkgs_no_src),
           'pkgs_no_spec': sorted(_pkgs_no_spec),
           'pkgs_with_spec': sorted(_pkgs_with_spec),
           'pkgs_with_src': sorted(_pkgs_with_src),
           'pkgs_nice': _pkgs_nice}
    return rez


def check_deb_in_git_v2(git_list, debs, cfg):
    """
    Check that deb exist in git's. KISS
    Whole structure hardcoded for `openstack` and `specs`
    debs = {
    }
    """

    _specs = []
    for k in git_list['specs'].keys(): _specs.append(k.split('/')[-1])
    _openstack = []
    for k in git_list['openstack'].keys(): _openstack.append(k.split('/')[-1])
    # _src = []
    # for p in deb_pkgs.keys(): _src.append((deb_pkgs[p]['source']))
    # _uniq_src = set(_src)
    #
    _n_src = {}
    # uniq list by deb source
    for p in debs.keys():
        _n_src[debs[p]['source_name']] = {
            'Private-Mcp-Code-Sha': debs[p]['Private-Mcp-Code-Sha'],
            'Private-Mcp-Spec-Sha': debs[p]['Private-Mcp-Spec-Sha']
        }
    _pkgs_no_spec = []
    _pkgs_no_src = []
    _pkgs_with_spec = []
    _pkgs_with_src = []
    _pkgs_nice = {}
    # FIXME hardcoode
    _black_spec = cfg['targets']['specs'].get('project_blacklist', [])
    _black_src = cfg['targets']['openstack'].get('project_blacklist', [])
    _git_src_prefix = cfg['targets']['openstack'].get('prefixes', [])[0]
    _git_spec_prefix = cfg['targets']['specs'].get('prefixes', [])[0]
    if len(cfg['targets']['openstack'].get('prefixes', [])) > 1 or len(cfg['targets']['specs'].get('prefixes', [])) > 1:
        LOG.error("I cant work with multiply prefixes ;(")
        sys.exit(1)
    for p in _n_src.keys():
        # Check that related deb pkg 'source:' in git specs
        if p in _black_spec and p in _specs:
            LOG.info("Blacklisted from specs:{}".format(p))
        elif p not in _specs:
            LOG.error("Not in specs:{}".format(p))
            _pkgs_no_spec.append(p)
        else:
            _pkgs_with_spec.append(p)
            # God bless that source: == last part of string!
            _specs_path = [k for k in git_list['specs'] if k.endswith(p)]
            if len(_specs_path) > 1:
                LOG.warning("Fix duplicate SPECS PATH manually:{}".format(_specs_path))
            _pkgs_nice[p] = {
                'specs': {
                    'path': _specs_path,
                    'Private-Mcp-Spec-Sha': _n_src[p]['Private-Mcp-Spec-Sha'],
                    'branches': list(
                        git_list['specs'][os.path.join(_git_spec_prefix, p)][
                            'branches'].keys())}}
        # Check that related deb pkg 'source:' in git sources
        if p in _black_src and p in _openstack:
            LOG.info("Blacklisted from sources:{}".format(p))
        if p not in _openstack:
            LOG.warning("Not in soures:{}".format(p))
            _pkgs_no_src.append(p)
        else:
            # God bless that source: == last part of string!
            _pkgs_with_src.append(p)
            # If pkgs missed from specs - it would fail to add source key
            if not _pkgs_nice.get(p, False):
                _pkgs_nice[p] = {}
            # FIXME check for overwrite!
            _pkgs_nice[p]['source'] = [k for k in git_list['openstack'] if
                                       k.endswith(p)]
            # Check for not work k.endswith magic
            _src_path = [k for k in git_list['openstack'] if k.endswith(p)]
            if len(_src_path) > 1:
                LOG.warning("Fix duplicate SOURCE PATH manually:{}".format(_src_path))
            _pkgs_nice[p]['source'] = {
                'path': _src_path,
                'Private-Mcp-Code-Sha': _n_src[p]['Private-Mcp-Code-Sha'],
                'branches': list(
                    git_list['openstack'][os.path.join(_git_src_prefix, p)][
                        'branches'].keys())}

    rez = {'pkgs_no_src': sorted(_pkgs_no_src),
           'pkgs_no_spec': sorted(_pkgs_no_spec),
           'pkgs_with_spec': sorted(_pkgs_with_spec),
           'pkgs_with_src': sorted(_pkgs_with_src),
           'pkgs_nice': _pkgs_nice}
    return rez


def parse_ubuntu_ups(pkgs):
    # ux = parse_list("lists/upstream-ubuntu-xenial")
    lfiles = ["upstream-ubuntu-xenial-main",
              "upstream-ubuntu-xenial-multiverse",
              "upstream-ubuntu-xenial-restricted",
              "upstream-ubuntu-xenial-universe"]
    uxu = {}
    for lfile in lfiles:
        save_file = "/tmp/{}.yaml".format(lfile)
        if os.path.isfile(save_file):
            uxu = ut.dict_merge(uxu, ut.read_yaml(save_file))
            LOG.warning("Cache used: {}".format(save_file))
        else:
            chunk = parse_list("lists/{}".format(lfile))
            ut.save_yaml(chunk, save_file)
            uxu = ut.dict_merge(uxu, chunk)
    # ipdb.set_trace()
    not_in_ubuntu = []
    uxu_source = pkgs_list_by_sources(uxu)
    # ipdb.set_trace()
    for k in pkgs.keys():
        if k not in uxu_source.keys():
            not_in_ubuntu.append(k)
            LOG.info("Pkgs: {} not exist in ubuntu-xenial upstream".format(k))
    # ipdb.set_trace()
    _z = set(not_in_ubuntu)
    return _z, uxu

def pkgs_list_by_sources(parsed_list):
    """
    return sorted by source
    """
    # collect all sources
    rez = {}
    for pkg in parsed_list.keys():
      ipdb.set_trace()
      # Should be refacted
      src = parsed_list[pkg]['source']
      k = ""
      rez[src] = {"pkgs" : [k for k in parsed_list.keys() if parsed_list[k]['source'] == src ],
                  'Private-Mcp-Code-Sha': parsed_list[k]['Private-Mcp-Code-Sha'],
                  'Private-Mcp-Spec-Sha': parsed_list[k]['Private-Mcp-Spec-Sha'],
                  'version': parsed_list[pkg]['version'],
                  'source': src }
    return rez

if __name__ == '__main__':
    # HOVNOSCRIPT!
    """
    SAVE_YAML=True CONFIG_FILE=config_infra.yaml ./run.py "lists/apt.os.pike.proposed"
    SAVE_YAML=True CONFIG_FILE=config_infra.yaml ./old_run.py "lists/apt.os.pike.2018.7.0-milestone1"
    """
    cfg = ut.read_yaml(cfgFile)
    list_file = ut.list_get(sys.argv, 1, 'os.pike.2018.7.0-milestone1')
    save_mask = os.path.join(
        "rez_" + list_file.replace('/', '_') + "_" + cfgFile.replace('.yaml',
                                                                     ""),
        "rez_" + list_file.replace('/', '_'))
    # save_to configs
    # will be masked like:
    # dump_to_file = NewGitrepoYamlMask + gen_cfgFile['targets'].keys() + '.yaml'
    # new_gitrepoCfgFile_packages.yaml

    _git_listfile = "{}_git_list.yaml".format(save_mask)
    if GERRIT_CACHE and os.path.isfile(_git_listfile):
        current_git_list = ut.read_yaml(_git_listfile)
        LOG.warning("Cache used :{}".format(_git_listfile))
    else:
        ipdb.set_trace()
        current_git_list = get_current_list(cfg)
        ut.save_yaml(current_git_list, _git_listfile)
    #
    deb_pkgs = parse_list(list_file)
    _zz = check_deb_in_git(current_git_list)
    pkgs_no_src = _zz['pkgs_no_src']
    pkgs_no_spec = _zz['pkgs_no_spec']
    pkgs_with_spec = _zz['pkgs_with_spec']
    pkgs_with_src = _zz['pkgs_with_src']
    pkgs_nice = _zz['pkgs_nice']
    ipdb.set_trace()

    deb_pkgs_by_source = pkgs_list_by_sources(deb_pkgs)

    #pkgs_not_in_ubuntu,_ = parse_ubuntu_ups(pkgs_nice)
    ##
    if not SAVE_YAML:
        LOG.info("Not going to save anything,Ciao!")
        sys.exit(0)

    # save
    ut.save_yaml(pkgs_no_src, "{}_pkgs_no_src.yaml".format(save_mask))
    ut.save_yaml(pkgs_no_spec, "{}_pkgs_no_spec.yaml".format(save_mask))
    ut.save_yaml(pkgs_with_spec, "{}_pkgs_with_spec.yaml".format(save_mask))
    ut.save_yaml(pkgs_with_src, "{}_pkgs_with_src.yaml".format(save_mask))
    ut.save_yaml(pkgs_nice, "{}_pkgs_nice.yaml".format(save_mask))
    #ut.save_yaml(pkgs_not_in_ubuntu, "{}_pkgs_not_in_ubuntu.yaml".format(save_mask))

    # save all from list
    ut.save_yaml(deb_pkgs, "{}_all.yaml".format(save_mask))
    ut.save_yaml(deb_pkgs_by_source, "{}_all_by_source.yaml".format(save_mask))
    # with any err
    pkgs_e = {}
    for pkg in deb_pkgs.keys():
        if 'err' in deb_pkgs[pkg].values():
            pkgs_e[pkg] = deb_pkgs[pkg]
    ut.save_yaml(pkgs_e, "{}_with_any_err.yaml".format(save_mask))

    # with err in priv_spec
    pkgs_priv_spec_e = {}
    for pkg in deb_pkgs.keys():
        if 'err' in deb_pkgs[pkg]['Private-Mcp-Spec-Sha']:
            pkgs_priv_spec_e[pkg] = deb_pkgs[pkg]
    ut.save_yaml(pkgs_priv_spec_e,
                 "{}_with_spec_err.yaml".format(save_mask))

    # with err in priv_code
    pkgs_priv_code_e = {}
    for pkg in deb_pkgs.keys():
        if 'err' in deb_pkgs[pkg]['Private-Mcp-Code-Sha']:
            pkgs_priv_code_e[pkg] = deb_pkgs[pkg]
    ut.save_yaml(pkgs_priv_code_e,
                 "{}_with_code_err.yaml".format(save_mask))
    #
