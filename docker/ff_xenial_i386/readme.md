firefox x32, in xenial docker
=================

## Table of Contents

- [Build](#build)
- [Run](#run)

### 1) Build ubuntu x32 itself

```bash
$ cd ../ubuntu_16_i386/ 
$ wget https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-i386-root.tar.gz
$ docker build -t xenial_i386 .
```
### 2) Build ff_xenial_i386
```bash
$ cd ../ff_xenial_i386/
$ vim Dockerfile # and replace *uid=1000 gid=1000* with your user / group id
$ docker build -t ff_386 .

```
### 3) Enable TCP pulse using manual:
More info about sound pass [here](http://stackoverflow.com/questions/28985714/run-apps-using-audio-in-a-docker-container "link")

### 4) One-shot run:
```bash
#!/bin/bash
docker run -it --net host --memory 2048mb \
 -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY \
 -v /dev/shm:/dev/shm \
 -v /run/user/1000/pulse:/run/user/1001/pulse \
 -v /var/lib/dbus:/var/lib/dbus \
 -v ~/.pulse:/home/developer/.pulse \
 -e PULSE_SERVER=tcp:$(hostname -i):4713 \
 -e PULSE_COOKIE=/run/pulse/cookie \
 -e DISPLAY=unix$DISPLAY \
 -v ~/.config/pulse/cookie:/run/pulse/cookie ff_386 firefox --no-remote about:plugins 

```
## Warning

For some reason, at least on ubuntu14.04 + mate, sometimes pulseaudio may hang
 after container stop, like work-around we can use:

```bash
#!/bin/bash
pulseaudio --cleanup-shm
xhost +
docker run -it --net host --memory 2048mb \
 --rm \
 -v /tmp/.X11-unix:/tmp/.X11-unix \
 -v /dev/shm:/dev/shm \
 -v /run/user/1000/pulse:/run/user/1001/pulse \
 -v /var/lib/dbus:/var/lib/dbus \
 -v ~/.pulse:/home/developer/.pulse \
 -e PULSE_SERVER=tcp:$(hostname -i):4713 \
 -e PULSE_COOKIE=/run/pulse/cookie \
 -e DISPLAY=$DISPLAY \
 -v ~/.config/pulse/cookie:/run/pulse/cookie ff_386 firefox --no-remote about:plugins 
xhost -
pulseaudio --cleanup-shm
pulseaudio --kill
pulseaudio --start
  
```

