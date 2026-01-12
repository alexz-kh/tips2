#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import subprocess,sys
import pprint as pprint
import json
pp = pprint.PrettyPrinter()

# Zabbix nvidia.smi.discovery LLD script
# Return format, if LLD:
"""
{
        "data":[

        {
                "{#GPU_UUID}":"GPU-03a3942c-cd19-3d04-3376-ec7bf66f3205",
                "{#GPU_ID}":"1"
        }

}
FYI:
uuid infomathion always static, otherwise "ID" could be changes if PCIe ports swapped
"""

DEBUG=False
nvidia_smi=" ".join(['nvidia-smi', '--format=csv,noheader'])

def parse_cli_args(args=None):

  usage_string = './get_nvidia_gpus.py [-h] <ARG> ...'



  parser = argparse.ArgumentParser(
      description='nvidia-smi wrapper tool',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
      usage=usage_string
  )

  parser.add_argument('-d', '--debug',
                         action='count',
                         help='Verbose output level. ')
  parser.add_argument('--mode', dest='mode', type=str,
                         help='discovery OR query')
  parser.add_argument('--query', dest='query', type=str,
                         help='temperature.gpu')
  parser.add_argument('--gpu_uuid',
                             type=str,
                             dest='uuid',
                             help='Query for --query: '
                                  'Example:temperature.gpu\npower.draw ')
  parser.add_argument('--gpu_id',
                             type=str,
                             help='Query for --query: '
                                  'Example:temperature.gpu\npower.draw ')
  if len(sys.argv[1:])==0:
    parser.print_help()
    sys.exit(1)

  return parser.parse_args(args=args)

def run_c(command):
  child = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
  child.wait()
  out,err = child.communicate()
  if DEBUG:
    print '###Command: \n%s\n%s' % (command, out)
  if err:
      print 'ERR:\n%s' % err
  return out,err

def collect_uuids():
  count=int(run_c(" ".join([nvidia_smi, '--query-gpu=count', '-i 0']))[0])
  gpu_data = []
  for gpu_id in range(0,count):
    gpu_uuid=run_c(" ".join([nvidia_smi,'--query-gpu=uuid', '-i {0}'.format(gpu_id)]))[0].replace('\n','')
    gpu_data.append({"{#GPU_UUID}": gpu_uuid, "{#GPU_ID}": gpu_id})
  return gpu_data

def collect_uuids_and_temp():
  """
  return: {{"GPU_UUID" : "GPU_TEMP"}}
  """
  gpu_data = {}
  gpus=filter(None,run_c(" ".join([nvidia_smi,'--query-gpu=uuid,temperature.gpu']))[0].split('\n'))
  for gpu in gpus:
    _gpu, _temp = str(gpu.split(',')[0]),int(gpu.split(',')[1])
    gpu_data[_gpu] = _temp
  return gpu_data

def get_temp_by_uuid(uuid):
  data=collect_uuids_and_temp()
  return data.get(uuid,"NoSuchGpuID")

def main():
  if args_.mode == "query":
    if args_.query == "temperature.gpu":
      print(get_temp_by_uuid(args_.uuid))
    else:
      print "QueryNotSupport"
      sys.exit(1)
  elif args_.mode == "discovery":
    data = { "data": collect_uuids() }
    print json.dumps(data)

if __name__ == '__main__':
   args_ = parse_cli_args()
   main()

