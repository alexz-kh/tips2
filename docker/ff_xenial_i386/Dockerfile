FROM xenial_i386

RUN cd /etc/apt/; echo "deb http://cz.archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse\ndeb http://cz.archive.ubuntu.com/ubuntu/ xenial-updates main restricted universe multiverse\n" > sources.list

#RUN echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" >> /etc/apt/sources.list
RUN echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
RUN echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections
RUN add-apt-repository -y ppa:webupd8team/java
RUN apt-get update
RUN apt-get install -y oracle-java8-installer && apt-get install -y firefox vim libgl1-mesa-glx pulseaudio libxv1 libxmu6 libgcj16-awt

# Replace 1000 with your user / group id
RUN export uid=1000 gid=1000 && \
    mkdir -p /home/developer && \
    echo "developer:x:${uid}:${gid}:Developer,,,:/home/developer:/bin/bash" >> /etc/passwd && \
    echo "developer:x:${uid}:" >> /etc/group && \
    echo "developer ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/developer && \
    chmod 0440 /etc/sudoers.d/developer && \
    chown ${uid}:${gid} -R /home/developer

USER developer
ENV HOME /home/developer
CMD /bin/bash
#CMD /usr/bin/firefox
