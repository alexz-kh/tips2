#!/usr/bin/env python
# -*- coding: utf-8 -*-

from github import Github
import logging as LOG
import time

LOG.basicConfig(level=LOG.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                format='%(asctime)-15s - [%(levelname)s] %(module)s:%(lineno)d: '
                       '%(message)s', )

import ipdb

def gather_clone_urls(organization, no_forks=True):
    all_repos = gh.repos.list_by_org(user=organization, type='all').all()
    for repo in all_repos:
        # Don't print the urls for repos that are forks.
        if no_forks and repo.fork:
            continue
        yield repo.clone_url


if __name__ == '__main__':

    o_name = 'salt-formulas'
    token = '1111111111'
    g = Github(login_or_token=token)
    org = g.get_organization(o_name)
    repos = org.get_repos()
#    ipdb.set_trace()
    #reponames = sorted(repo.name for repo in repos)
    #print(reponames)
    nope = []
    for repo in repos:
        LOG.info("Process repo:{0}".format(repo.name))
        try:
            listing = repo.get_contents(path='/')
        except:
            LOG.warning("Something wrong with repo: {}".format(repo.name))
            continue
            pass
        files = [ f.name for f in listing ]
        if 'debian' not in files:
            nope.append(repo.name)
            LOG.warning("Repo:{0} w\o debian folder".format(repo.name))
            LOG.info("Result:\n{}".format(nope))
            time.sleep(1)
    LOG.info("Result:\n{}".format(nope))

