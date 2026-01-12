# Flow

get all uuid => spawn items via "propotype" => get temp by id

# Zabbix conf.d conf

```
UserParameter=nvidia.smi.guery[*],bash -c '/etc/zabbix/get_nvidia_gpus.py --mode query --query $2 --gpu_uuid $1 '
UserParameter=nvidia.smi.discovery,bash -c '/etc/zabbix/get_nvidia_gpus.py --mode discovery'
```

# Openwrt ping:
Manual:

[with_wifi](https://blog.xsk.in/it/monitoring-openwrt-v-zabbix/590)
```
opkg install sudo zabbix-agentd
echo "zabbix ALL=(root) NOPASSWD: /bin/ping" >> /etc/sudoers.d/zabbix
```

# TODO

rewrite with
[nvidia-ml-py](https://pypi.python.org/pypi/nvidia-ml-py/)

[man](https://pythonhosted.org/nvidia-ml-py/)
