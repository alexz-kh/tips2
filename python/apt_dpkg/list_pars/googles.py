#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os
import datetime,pytz
import pprint as pprint
import logging, logging.config
import lib as ut
import run_apt_pkg as aptr

from gspread import utils as gutil
import pygsheets

USE_DPKG_CACHE = os.environ.get("USE_DPKG_CACHE", "/tmp/archive_pkgs_by_source.yaml")
API_KEY  = os.environ.get("API_KEY", "/home/alexz/.ssh/gsheet.py.txt")
GS_ID    = os.environ.get("GS_ID",'1x88N2nTVsvo82GBeRGVJnUnz_JIjDHQ5uPjybjHZbe4')


# https://habr.com/post/305378/
# https://raw.githubusercontent.com/Tsar/Spreadsheet/master/Spreadsheet.py

try:
  import ipdb
except ImportError:
  print("no ipdb")


def color_me(color):
    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"

    color_seq = COLOR_SEQ % (30 + color)

    def closure(msg):
        return color_seq + msg + RESET_SEQ
    return closure


class ColoredFormatter(logging.Formatter):
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    colors = {
        'INFO': color_me(WHITE),
        'WARNING': color_me(YELLOW),
        'DEBUG': color_me(BLUE),
        'CRITICAL': color_me(YELLOW),
        'ERROR': color_me(RED)
    }

    def __init__(self, msg, use_color=True, datefmt=None):
        logging.Formatter.__init__(self, msg, datefmt=datefmt)
        self.use_color = use_color

    def format(self, record):
        orig = record.__dict__
        record.__dict__ = record.__dict__.copy()
        levelname = record.levelname

        prn_name = levelname + ' ' * (8 - len(levelname))
        if levelname in self.colors:
            record.levelname = self.colors[levelname](prn_name)
        else:
            record.levelname = prn_name

        # super doesn't work here in 2.6 O_o
        res = logging.Formatter.format(self, record)

        # res = super(ColoredFormatter, self).format(record)

        # restore record, as it will be used by other formatters
        record.__dict__ = orig
        return res


def setup_loggers(name=__name__, log_path=None):
    log_config = {
        'version': 1,
        'formatters': {
            'default': {'format': '%(asctime)s - %(levelname)s - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            'default': {
                'level': 'DEBUG',
                'handlers': ['console']
            }
        },
        'disable_existing_loggers': False
    }
    file_h = {
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': log_path,
                'maxBytes': 1024,
                'backupCount': 3
            }
        },
        'loggers': {
            'default': {
                'handlers': ['file', 'console' ]
            }
        },
        'disable_existing_loggers': False
    }
    if log_path:
        log_config = ut.dict_merge(log_config,file_h)
    logging.config.dictConfig(log_config)

    return logging.getLogger(name)


#/////////////////////////////////////////////////////////////////////////////#
def get_timestamp():
    _d = datetime.datetime.utcnow()
    d_with_timezone = _d.replace(tzinfo=pytz.UTC)
    return d_with_timezone.isoformat('T')


@ut.retry(Exception, tries=4, delay=102)
def process_source_row(_pkg, row, archive=None):
    """
    TBD
    1) Update range, if exist
    2) Hihlight new
    :return last used row number
    """
    if not archive:
        LOG.error('Archive not passed!')
        sys.exit(1)
    columer = {'nightly': 2, 'proposed': 3, 'testing': 4, 'uca': 5}
    #ipdb.set_trace()
    pkg_range_name = 'range_' + _pkg['source_name'].replace('-', '_').replace(
        '.', '_')
    pkg_range = get_row_datarange(pkg_range_name)
    if not pkg_range:
        '''
         insert one row, to not overwrite prev.
        '''
        row += 1
        wks.insert_rows(row=row - 1, number=1)
        pkg_range = create_named_row(pkg_range_name, row, x_start,
                                     len(header))
        pkg_range[0].color = c_light_red
        LOG.info('Created new range: {} at row:{}'.format(pkg_range_name, row))
    elif pkg_range[0].color != c_none:
        pkg_range[0].color = c_none
    LOG.info('process_source_row start: {}'
             ' x_start:{} row:{}'.format(_pkg['source_name'], x_start, row))
    _pkgs = '\n'.join(_pkg['pkgs'])
    column = columer.get(archive, None)
    if archive in ['nightly', 'proposed', 'testing']:
        mcp_value = "Version:{}\n" \
                    "Code:{}\n" \
                    "Spec:{}".format(_pkg['version'],
                                     _pkg[
                                         'Private-Mcp-Code-Sha'],
                                     _pkg[
                                         'Private-Mcp-Spec-Sha'])
    elif archive == 'uca':
        mcp_value = "Version:{}\n".format(_pkg['version'])
    else:
        LOG.error("Unexpected archive {}".format(archive))
        sys.exit(1)

    if pkg_range[0].value != _pkg['source_name']:
        pkg_range[0].value = _pkg['source_name']
    if pkg_range[1].value != _pkgs:
        pkg_range[1].value = _pkgs
    if pkg_range[column].value != mcp_value:
        pkg_range[column].value = mcp_value
        pkg_range[column].color = c_red
    elif pkg_range[column].color != c_none:
        pkg_range[column].color = c_none
    LOG.info('process_source_row end: {}'
             ' x_start:{} row:{}'.format(_pkg['source_name'], x_start, row))
    return row


def get_row(row,col_s,col_e):
    return wks.get_values((row, col_s), (row, col_e), returnas='cells', include_empty_rows=True)[0]

@ut.retry(Exception, tries=3, delay=102)
def get_row_datarange(range_name):
    row = None
    try:
        row = wks.get_named_range(range_name)[0]
    except pygsheets.exceptions.RangeNotFound:
        LOG.info("Range: {} not found".format(range_name))
        pass
    return row


@ut.retry(Exception, tries=3, delay=120)
def create_named_row(range_name, row, col_start, col_end=None):
    """
    Work per row
    """
    if not col_end:
         col_end = col_start
    _s = gutil.rowcol_to_a1(row, col_start)
    _e = gutil.rowcol_to_a1(row, col_end)
    return wks.create_named_range(range_name, _s, _e )[0]


@ut.retry(Exception, tries=3, delay=120)
def process_header_row():
    LOG.info('Updating header_row')
    # FIXME
    if wks.cell('A1').value != 'Last update:':
        wks.cell('A1').value = 'Last update:'
    wks.cell('B1').value = 'NOW'
    wks.cell('B1').color = c_red
    header_row = get_row_datarange('range_header_row')
    if not header_row:
        header_row = create_named_row('range_header_row', y_start, x_start,
                                      len(header))
    for c, v in zip(header_row, header):
        if c.color != c_orange:
            c.color = c_orange
        if c.value != v:
            c.value = v

@ut.retry(Exception, tries=3, delay=120)
def clean_all():
    wks.clear()
    for nr in wks.get_named_ranges():
        wks.delete_named_range(nr.name)


if __name__ == '__main__':

    LOG = setup_loggers()
    # Disable noise logs
    logging.getLogger('pygsheets').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)

    gc = pygsheets.authorize(service_file=API_KEY)
    # spreadsheet
    sh = gc.open_by_key(GS_ID)
    # worksheet
    wks = sh.sheet1
    c_orange = (1, 0.6, 0, 0)
    c_red = (1.0, 0, 0, 0)
    c_none = (1, 1, 1, 1)
    c_light_red = (0.5, 0, 0, 0)

    """

    """
    header = ['Source','Pkgs','nightly','testing','proposed','uca','SRC-repo','SPEC-repo' ]
    y_start = 5
    x_start = 1

    # clean_all()
    process_header_row()
    #ipdb.set_trace()

    if os.path.isfile(USE_DPKG_CACHE):
        archives = ut.read_yaml(USE_DPKG_CACHE)
        LOG.warning("USE_DPKG_CACHE used:{}".format(USE_DPKG_CACHE))
    else:
        archives = {'nightly': aptr.get_one_list(['apt_os_pike_nightly_main']),
                    'testing': aptr.get_one_list(['apt_os_pike_testing_main']),
                    'proposed': aptr.get_one_list(
                        ['apt_os_pike_proposed_main']),
                    'uca': aptr.get_one_list(['uca_queens_xenial_upd_main',
                                              'uca_queens_xenial_main'],
                                             private=False)}
        ut.save_yaml(archives, USE_DPKG_CACHE)
    #ipdb.set_trace()
    row_n = y_start + 1


    # LOG.info("Getting all_pkg_ranges")
    # _anamed = wks.get_named_ranges()
    # all_pkg_ranges = [r.name for r in _anamed]


    def process_one_archive(all_pkgs, row, _archive):
        # ipdb.set_trace()
        t_row = row
        for pname in sorted(all_pkgs.keys()):
            #ipdb.set_trace()
            if t_row > 10:
                LOG.info("zzz")
                break
            LOG.info('Processings \n{}'
                     '\n row: {}'
                     '\n archive:{}'.format(all_pkgs[pname], t_row,
                                            _archive))
            #ipdb.set_trace()
            t_row = process_source_row(all_pkgs[pname], t_row,
                                     archive=_archive)


    for archive in sorted(archives.keys()):
        # for archive in sorted(archives.keys()):
        LOG.info("Archive:{}".format(archive))
        deb_pkgs_by_source = archives[archive]
        process_one_archive(deb_pkgs_by_source, row_n,
                            _archive=archive.lower())




    wks.cell('B1').value = get_timestamp()
    wks.cell('B1').color = c_none
    #ipdb.set_trace()

    LOG.info("Done")
    sys.exit(0)


