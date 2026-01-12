

# 1)  Build container:
wget https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-i386-root.tar.gz
# 2) Fix in Dockerfile gid and uid and build it
docker build -t ff_386 

# 3) Enable TCP pulse using manual:
# http://stackoverflow.com/questions/28985714/run-apps-using-audio-in-a-docker-container

# 4) Fix in cmd gid and uid also, and run it finally
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

