#!/usr/bin/python


"""
 http://apt.alioth.debian.org/python-apt-doc/library/apt_pkg.html#example-find-all-missing-dependencies
 https://help.ubuntu.com/community/Repositories
"""
import pprint,sys
try:
    import apt_pkg,apt
except ImportError:
    print "Error importing apt_pkg, is python-apt installed?"
    sys.exit(1)

ppr = pprint.PrettyPrinter(indent=2)

def zz2():
    all_pkgs={}
    filtered_pkgs={}
    for pkg in sorted(all_cache.packages, key=lambda pkg: pkg.name):
        # pkg is from a list of packages, sorted by name.
        if pkg.name not in installed.keys():
          continue
        for version in pkg.version_list:
            #import ipdb;ipdb.set_trace()
            # We need exactly installed version
            if pkg.current_ver.ver_str != version.ver_str:
              #print("False version:{} '{}'".format(pkg.name,version.ver_str))
              continue
            for pfile, _ in version.file_list:
                all_pkgs[pkg.name] = { "version" : pkg.current_ver.ver_str,
                                       "section" : pkg.current_ver.section,
                                       "origin" : pfile.origin.lower(),
                                       "component" : pfile.component.lower(),
                                       "archive": pfile.archive.lower() }
                if (pfile.origin.lower() == "ubuntu xenial" and not pfile.component.startswith("main") and pfile.archive in ["xenial", 'xenial-security', "xenial-updates"]):
                    # We only want packages from Debian unstable main.
                    filtered_pkgs[pkg.name] = { "version" : pkg.current_ver.ver_str,
                                                "section" : pkg.current_ver.section,
                                                "origin" : pfile.origin.lower(),
                                                "component" : pfile.component.lower(),
                                                "archive": pfile.archive.lower() }
                    break
    return filtered_pkgs,all_pkgs


def all_installed():
  pkgs={}
  for mypkg in apt.Cache():
      if cache[mypkg.name].is_installed:
          pkgs[mypkg.name] = mypkg.installed.version
  return pkgs


if __name__ == '__main__':
    apt_pkg.init()
    apt_pkg.init_config()
    apt_pkg.init_system()

    all_cache = apt_pkg.Cache()

    cache = apt.Cache()
    #cache.update()
    cache.open()
    #dcache = apt_pkg.DepCache(apt_pkg.Cache())

    installed=all_installed()
    filtered_pkgs,all_pkgs=zz2()

    print("Installed count: {}".format(len(all_pkgs.keys())))
    print("Sorted count: {}".format(len(filtered_pkgs.keys())))
    print("Sorted list:\n")
    ppr.pprint(filtered_pkgs)



    sys.exit(0)
