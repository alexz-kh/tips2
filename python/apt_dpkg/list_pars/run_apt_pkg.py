#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
https://askubuntu.com/questions/578257/how-to-get-the-package-description-using-python-apt
https://apt.alioth.debian.org/python-apt-doc/library/index.html
"""
import apt
import apt_pkg
from aptsources.sourceslist import SourcesList
import tempfile, os, sys
import six
import copy
from pprint import pprint, pformat
import logging as LOG
from datetime import datetime

import lib as ut
import old_run as old
import ipdb

try:
    import ipdb
except ImportError:
    print("no ipdb")

LOG.basicConfig(level=LOG.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                format='%(asctime)-15s - [%(levelname)s] %(module)s:%(lineno)d: '
                       '%(message)s', )

cfgFile = os.environ.get("CONFIG_FILE", "config_infra.yaml")
SAVE_YAML = ut.str2bool(os.environ.get("SAVE_YAML", True))
GERRIT_CACHE = ut.str2bool((os.environ.get("GERRIT_CACHE", True)))

#########
REPOS = {
    'apt_xenial_testing_salt': {
        "type": 'deb',
        "uri": 'http://apt.mirantis.com/xenial',
        "dist": 'testing',
        "orig_comps": ['salt'],
        "comment": 'qwe',
    },
    'apt_xenial_2018.4.0_salt': {
        "type": 'deb',
        "uri": 'http://apt.mirantis.com/xenial',
        "dist": '2018.4.0',
        "orig_comps": ['salt'],
        "comment": 'qwe',
    },
    'apt_os_pike_nightly_main': {
        "type": 'deb',
        "uri": 'http://apt.mirantis.com/xenial/openstack/pike/',
        "dist": 'nightly',
        "orig_comps": ['main'],
        "comment": 'os.pike.nightly'
    },
    'apt_os_pike_testing_main': {
        "type": 'deb',
        "uri": 'http://apt.mirantis.com/xenial/openstack/pike/',
        "dist": 'testing',
        "orig_comps": ['main'],
        "comment": 'os.pike.testing'
    },
    'apt_os_pike_proposed_main': {
        "type": 'deb',
        "uri": 'http://apt.mirantis.com/xenial/openstack/pike/',
        "dist": 'proposed',
        "orig_comps": ['main'],
        "comment": 'os.pike.proposed'
    },
    'uca_queens_xenial_upd_main': {
        "type": 'deb',
        "uri": 'http://ubuntu-cloud.archive.canonical.com/ubuntu',
        "dist": 'xenial-updates/queens',
        "orig_comps": ['main'],
        "comment": 'uca_queens_main'
    },
    'uca_queens_xenial_main': {
        "type": 'deb',
        "uri": 'http://ubuntu-cloud.archive.canonical.com/ubuntu',
        "dist": 'xenial-updates/queens',
        "orig_comps": ['main'],
        "comment": 'uca_queens_main'
    },
    'apt_xenial_nightly_extra': {
        "type": 'deb',
        "uri": 'http://apt.mirantis.com/xenial/',
        "dist": 'nightly',
        "orig_comps": ['extra'],
        "comment": 'extra_main'
    }

}
#########

APT_DIRS = [
    "etc/apt/sources.list.d",
    "etc/apt/preferences.d",
    "var/lib/apt/lists",
    "var/lib/dpkg",
]

APT_FILES = [
    "etc/apt/apt.conf",
    "etc/apt/sources.list",
    "var/lib/dpkg/status",
]

APT_CONF_ENTRIES = {
    'Dir': '{rootdir}',
    'Debug::pkgProlemResolver': 'true',
    'APT::Architectures': '{arch}',
    'APT::Install-Recommends': 'false',
    'APT::Get::AllowUnauthenticated': 'true',
    'Acquire::AllowInsecureRepositories': 'true',
    'Acquire::AllowDowngradeToInsecureRepositories': 'true',
}


def gen_repo_aptly(dist, orig, postfix=''):
    # dist = '2018.7.0-milestone1' / nightly
    # orig = ['extra', 'salt']
    uri = os.path.join('http://apt.mirantis.com/xenial/', postfix)
    rez = {
        "type": 'deb',
        "uri": uri,
        "dist": dist,
        "orig_comps": orig,
        "comment": "{}:{}".format(dist, orig)
    }
    return rez


def gen_repo_mirror_update(release, repo, dist='xenial', orig=['main']):
    # dist = '2018.7.0-milestone1' / nightly
    # orig = ['extra', 'salt']
    # release = proposed
    # repo = openstack-pike

    uri = os.path.join('http://mirror.mirantis.com/update/', release, repo,
                       dist)
    #    uri = os.path.join('http://mirror.mirantis.com/', release, repo, dist)
    rez = {
        "type": 'deb',
        "uri": uri,
        "dist": dist,
        "orig_comps": orig,
        "comment": "{}:{}".format(dist, orig)
    }
    return rez


def gen_repo_mirror(release, repo, dist='xenial', orig=['main']):
    # dist = '2018.7.0-milestone1' / nightly
    # orig = ['extra', 'salt']
    # release = proposed
    # repo = openstack-pike

    uri = os.path.join('[target-=Contents-deb] http://mirror.mirantis.com/', release, repo)
    rez = {
        "type": 'deb',
        "uri": uri,
        "dist": dist,
        "orig_comps": orig,
        "comment": "{}:{}".format(dist, orig)
    }
    return rez


def setup_apt(rootdir):
    # Create APT structure
    for x in APT_DIRS:
        os.makedirs(os.path.join(rootdir, x))

    # Touch APT files
    for x in APT_FILES:
        open(os.path.join(rootdir, x), "w").close()

    # Generate apt.conf
    apt_conf_path = os.path.join(rootdir, "etc/apt/apt.conf")
    os.putenv('APT_CONFIG', apt_conf_path)
    apt_conf_opts = {
        'arch': os.environ.get("ARCH", "amd64"),
        'rootdir': rootdir,
    }
    with open(apt_conf_path, "w") as f:
        for key in APT_CONF_ENTRIES.keys():
            f.write('{} "{}";'.format(key, APT_CONF_ENTRIES[key].format(
                **apt_conf_opts)) + '\n')
            f.write('APT{Ignore {"gpg-pubkey"; }}; ')
            f.flush()

    # Init global config object
    apt_pkg.init_config()
    apt_pkg.read_config_file(apt_pkg.config, apt_conf_path)
    apt_pkg.init_system()

    return apt_conf_path


def get_pkgs(_cache, return_all_v=False):
    """
    cache should contain only one source - unless 'duplicates' check useless.
    Return: always 'candidate' version will be.
    """
    pkgs = {}
    dupl = {}
    for pkg in _cache:
        if len(pkg.versions) > 1:
            dupl[pkg.name] = {}
            for v in pkg.versions.keys():
                dupl[pkg.name][v] = pkg.versions[v].origins
            LOG.error("multiply versions"
                      "detected:{}\n{}".format(pkg.name, pformat(pkg.versions)))
        if return_all_v:
            all_v = {}
            for v in pkg.versions.keys():
                all_v[v] = {'source_name': pkg.versions[v].source_name,
                            'archive': pkg.versions[v].origins[0].archive,
                            'Private-Mcp-Spec-Sha': pkg.versions[v].record.get(
                                'Private-Mcp-Spec-Sha', None),
                            'Private-Mcp-Code-Sha': pkg.versions[v].record.get(
                                'Private-Mcp-Code-Sha', None)}
            pkgs[pkg.name] = {'versions': all_v}
        # Candidate, might not always be 'latest' - its depends on apt priorit.
        latest_v = pkg.candidate
        pkgs[pkg.name] = {'source_name': latest_v.source_name,
                          'archive': latest_v.origins[0].archive,
                          'version': latest_v.version,
                          'Private-Mcp-Spec-Sha': latest_v.record.get(
                              'Private-Mcp-Spec-Sha', None),
                          'Private-Mcp-Code-Sha': latest_v.record.get(
                              'Private-Mcp-Code-Sha', None)
                          }
    return pkgs, dupl


def sort_by_source(pkgs):
    """
    Always guessing from one version, so work only over 'version' key
    """
    _pkgs = copy.deepcopy(pkgs)
    rez = {}
    k = ""
    for pkg in _pkgs.keys():
        # Always for 1st version
        src = _pkgs[pkg]['source_name']
        k = ""
        rez[src] = {
            "pkgs": [k for k in _pkgs.keys() if _pkgs[k]['source_name'] == src],
            'archive': _pkgs[pkg]['archive'],
            'version': _pkgs[pkg]['version'],
            'Private-Mcp-Spec-Sha': _pkgs[pkg]['Private-Mcp-Spec-Sha'],
            'Private-Mcp-Code-Sha': _pkgs[pkg]['Private-Mcp-Code-Sha'],
            'source_name': src}
        rez[src]['pkgs'].sort()
    return rez


def process_salt_commit(pkgs_dict):
    """
    input:
    salt-formula-backupninja:
      archive: 2018.4.0
      pkgs:
      - salt-formula-backupninja
      source_name: salt-formula-backupninja
      version: 0.2+201803121530.124025c~xenial1
    output:
    salt-formula-backupninja:
      archive: 2018.4.0
      pkgs:
      - salt-formula-backupninja
      source_name: salt-formula-backupninja
      version: 0.2+201803121530.124025c~xenial1
      Private-Mcp-Code-Sha: 124025c

    :param pkgs_dict:
    :return:
    """
    result = copy.deepcopy(pkgs_dict)
    for pkg in result.keys():
        try:
            # facepalm ;(
            sha = 'error'
            if pkg == 'salt-formula-ceilometer':
                sha = result[pkg]['version'].split('-')[0].split('.')[-1]
            # elif pkg == 'salt-formula-swift':
            #                sha = '0031c7f'
            else:
                sha = \
                    result[pkg]['version'].split('+')[1].split('.')[1].split(
                        '~')[0]
            result[pkg]['Private-Mcp-Code-Sha'] = sha
            LOG.info('{}:{}'.format(pkg, sha))
        except IndexError:
            LOG.warning("Error to find sha pkg:{}".format(pkg))
            result[pkg]['Private-Mcp-Code-Sha'] = 'ERROR'
            pass
    return result


def get_one_list(listnames, private=True):
    """
    listnames=['{repo:data}']
    """
    import shutil

    adir = tempfile.mkdtemp()
    setup_apt(rootdir=adir)
    _sources_list = SourcesList()
    for l_name in listnames:
        _sources_list.add(**l_name)
    _sources_list.save()
    _cache = apt.Cache(rootdir=adir)
    _cache.update()
    _cache.open()
    _pkgs, _duplicates = get_pkgs(_cache)
    _s_source = sort_by_source(_pkgs)
    _cache.close()
    try:
        shutil.rmtree(adir)
        LOG.debug("Directory removed: {}".format(adir))
    except Exception as e:
        LOG.warning("Error: %s - %s." % (e.filename, e.strerror))
        pass
    if not private:
        for k in s_source.keys():
            _s_source[k].pop('Private-Mcp-Spec-Sha', None)
            _s_source[k].pop('Private-Mcp-Code-Sha', None)
    return _s_source, duplicates


def dump_aptly_openstack_simple(release, os_release='pike', to_dir=None):
    # Just return normal list, w\o gerrit magic
    # http://apt.mirantis.com/xenial/openstack/pike/ nightly main
    _postfix = 'openstack/{}/'.format(os_release)
    definition = gen_repo_aptly(release, ['main'], postfix=_postfix)
    _pkgs, _ = get_one_list([definition], private=True)
    if to_dir:
        ut.save_yaml(_pkgs,
                     "{}/apt_mirantis_openstack_{}_{}.yaml".format(to_dir,
                                                                   os_release,
                                                                   release))
    return _pkgs


def dump_mirantis_mirror(release, repo_dir, type, to_dir=None):
    # Magic for mirror.mirantis.com
    # Type - as dirt as possible hack for guess gerrit repo
    # ipdb.set_trace()
    os_pkgs, _ = get_one_list([gen_repo_mirror_update(release, repo_dir)],
                              private=True)
    cfg = ut.read_yaml(os.environ.get("CONFIG_FILE", "config_mcp.yaml"))
    _git_listfile = "{}/git_list.yaml".format(to_dir)
    if GERRIT_CACHE and os.path.isfile(_git_listfile):
        current_git_list = ut.read_yaml(_git_listfile)
        LOG.warning("Cache used :{}".format(_git_listfile))
    else:
        current_git_list = old.get_current_list(cfg)
        ut.save_yaml(current_git_list, _git_listfile)
    parsed = old.check_deb_in_git_v2(current_git_list, os_pkgs, cfg)

    if not to_dir:
        return
    for k in parsed.keys():
        ut.save_yaml(parsed[k],
                     "{}/mirror_"
                     "mirantis_{}_{}_chunk_{}.yaml".format(to_dir,
                                                           repo_dir,
                                                           release, k))
    merged = ut.dict_merge(os_pkgs, parsed['pkgs_nice'])
    # ipdb.set_trace()
    ut.save_yaml(merged,
                 "{}/mirror_mirantis_{}_{}_merged.yaml".format(to_dir,
                                                               repo_dir,
                                                               release))
    ut.save_yaml(os_pkgs,
                 "{}/mirror_mirantis_{}_{}_clean.yaml".format(to_dir,
                                                              repo_dir,
                                                              release))


def dump_aptly_openstack_junkie(release, os_release='pike', to_dir=None):
    # Maggic
    # http://apt.mirantis.com/xenial/openstack/pike/ nightly main
    _postfix = 'openstack/{}/'.format(os_release)
    definition = gen_repo_aptly(release, ['main'], postfix=_postfix)
    os_pkgs, _ = get_one_list([definition], private=True)
    #
    cfg = ut.read_yaml(cfgFile)
    _git_listfile = "{}/git_list.yaml".format(to_dir)
    if GERRIT_CACHE and os.path.isfile(_git_listfile):
        current_git_list = ut.read_yaml(_git_listfile)
        LOG.warning("Cache used :{}".format(_git_listfile))
    else:
        current_git_list = old.get_current_list(cfg)
        ut.save_yaml(current_git_list, _git_listfile)
    parsed = old.check_deb_in_git_v2(current_git_list, os_pkgs, cfg)

    if not to_dir:
        return
    for k in parsed.keys():
        ut.save_yaml(parsed[k],
                     "{}/apt_"
                     "mirantis_os_{}_{}_chunk_{}.yaml".format(to_dir,
                                                              os_release,
                                                              release, k))
    merged = ut.dict_merge(os_pkgs, parsed['pkgs_nice'])
    ut.save_yaml(merged,
                 "{}/apt_mirantis_os_{}_{}_merged.yaml".format(to_dir,
                                                               os_release,
                                                               release))
    ut.save_yaml(os_pkgs,
                 "{}/apt_mirantis_os_{}_{}_clean.yaml".format(to_dir,
                                                              os_release,
                                                              release))


def dump_aptly_salt(release, to_dir=False):
    # deb [arch=amd64] http://apt.mirantis.com/xenial nightly salt
    definition = gen_repo_aptly(release, ['salt'])
    _pkgs, _ = get_one_list([definition], private=False)
    salt_result = process_salt_commit(_pkgs)
    if to_dir:
        ut.save_yaml(salt_result,
                     "{}/apt_mirantis_salt_{}.yaml".format(to_dir, release))
    return _pkgs


def dump_ubuntu_mirror(release='update/proposed', to_dir=None):
    repo_dir = 'ubuntu'
    dists = ['xenial']  # , 'xenial-updates', 'xenial-security']
    orig = ['main']  # , 'restricted', 'universe']
    repo = []
    ipdb.set_trace()
    for dist in dists:
        repo.append(gen_repo_mirror(release, 'ubuntu', dist=dist, orig=orig))
    ipdb.set_trace()
    pkgs, _ = get_one_list(repo, private=False)


if __name__ == '__main__':
    dumpdir = tempfile.mkdtemp()
    # save_dir = 'rez_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    save_dir = 'rez_2'

    ipdb.set_trace()

    dump_ubuntu_mirror()
    # dump_mirantis_mirror('2019.2.0', 'openstack-pike', to_dir=save_dir, type='os')
    # Took from update already
    # dump_mirantis_mirror('proposed', 'openstack-pike', to_dir=save_dir, type = 'os')
    # dump_mirantis_mirror('2019.2.0', 'salt-formulas', to_dir=save_dir, type='formulas' )
    ipdb.set_trace()
    # pre 2019.2
    # dump_aptly_openstack_junkie('proposed', to_dir=save_dir)
    # dump_aptly_salt('2018.11.0', to_dir=save_dir)
    sys.exit(0)

    ipdb.set_trace()
    ####
    apt_conf_path = setup_apt(rootdir=rootdir)
    sources_list = SourcesList()
    #    sources_list.add(**REPOS['apt_os_pike_testing_main'])
    #    sources_list.add(**REPOS['apt_xenial_testing_salt'])
    #    sources_list.add(**REPOS['uca_queens_xenial_upd_main'])
    #    sources_list.add(**REPOS['uca_queens_xenial_main'])
    #    sources_list.add(**REPOS['apt_xenial_nightly_extra'])
    #    sources_list.add(**REPOS['apt_os_pike_proposed_main'])
    sources_list.add(**REPOS['apt_xenial_2018.4.0_salt'])
    sources_list.save()
    cache = apt.Cache(rootdir=rootdir)
    cache.update()
    cache.open()

    ipdb.set_trace()
    os_pike, _ = get_one_list(['apt_os_pike_proposed_main'])
    pkgs_os_pike_testing, duplicates = get_pkgs(cache)

    s_source = sort_by_source(pkgs_os_pike_testing)
    zz = {}
    for i in s_source.keys(): zz[i] = {'pkgs': s_source[i]['pkgs'],
                                       'version': s_source[i]['version']}
    ipdb.set_trace()
    ###############

    # HOVNOSCRIPT!
    """
    GERRIT_CACHE=True
    SAVE_YAML=True
    CONFIG_FILE=config_infra.yaml
    ./run.py "apt_os_pike_testing_main"
    """
    cfg = ut.read_yaml(cfgFile)
    # reponame = ut.list_get(sys.argv, 1, 'apt_os_pike_testing_main')

    # save_mask = os.path.join(
    #     "rez_" + reponame.replace('/', '_') + "_" + cfgFile.replace('.yaml',
    #                                                                  ""),
    #     "rez_" + reponame.replace('/', '_'))
    #
    # _git_listfile = "{}_git_list.yaml".format(save_mask)
    #
    # if GERRIT_CACHE and os.path.isfile(_git_listfile):
    #     current_git_list = ut.read_yaml(_git_listfile)
    #     LOG.warning("Cache used :{}".format(_git_listfile))
    # else:
    #     current_git_list = old.get_current_list(cfg)
    #     ut.save_yaml(current_git_list, _git_listfile)

    ipdb.set_trace()
    LOG.info("ZZ")
    if SAVE_YAML:
        ut.save_yaml(pkgs_os_pike_testing, "{}_pkgs_all.yaml".format(save_mask))
    ut.save_yaml(s_source, "{}_pkgs_by_source.yaml".format(save_mask))
    ut.save_yaml(duplicates, "{}_pkgs_duplicates.yaml".format(save_mask))
