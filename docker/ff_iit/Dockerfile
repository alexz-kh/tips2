# docker build --squash --no-cache --rm -t ff:latest .
# docker buildx --builder my_wide_builder build  --no-cache -t ff:latest --progress=plain --output type=docker .
# copy-pasted: https://gist.github.com/s3rj1k/daf5daa22720c22440f7cd092d483519
# docker run --rm --interactive --tty --net=host --device=/dev/bus/usb --device-cgroup-rule='c 189:* rmw' --init --env DISPLAY=$DISPLAY --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $XAUTH:/root/.Xauthority --name ff_b ff

# docker run --rm --interactive --tty --net=host --init --env DISPLAY=$DISPLAY --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $XAUTHORITY:/root/.Xauthority --name ff_b ff
FROM debian:bullseye

# IIT ff extension URI
ENV IIT_WEB_EXT_URI=https://eu.iit.com.ua/download/productfiles/eusw@iit.com.ua.xpi

# IIT PKCS#11 module URI
ENV IIT_PKCS_11=https://iit.com.ua/download/productfiles/euswi.64.deb

# Cabinet URI
ENV CABINET_URI=https://business.ukrsibbank.com/login

# DPKG none-interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# Install ff
RUN sed -i.bak 's/buster main/buster main contrib non-free/g' /etc/apt/sources.list && \
#      echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
      apt-get update && apt-get dist-upgrade -y &&  apt-get install --no-install-recommends -y \
        firefox-esr \
        libcanberra-gtk-module \
        libexif-dev \
        libpango1.0-0 \
        libv4l-0 \
        ca-certificates

# Install IIT PKCS#11 module
# https://iit.com.ua/download/productfiles/EUSignWebOManual.pdf
RUN apt-get install -y libccid \
                       opensc \
                       opensc-pkcs11 \
                       pcsc-tools \
                       pcscd \
                       procps \
                       usbutils \
                       wget --no-install-recommends && \
      wget ${IIT_PKCS_11} -O /tmp/euswi.64.deb && \
        dpkg -i /tmp/euswi.64.deb && \
          rm -f /tmp/euswi.64.deb

CMD set -ex ; pcscd; firefox "https://google.com" "${IIT_WEB_EXT_URI}" "${CABINET_URI}"
