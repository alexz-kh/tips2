Readme:

# Man:
[iso](https://fedoraproject.org/wiki/How_to_create_and_use_a_Live_CD)
[iso2pxe](http://www.livecd.ethz.ch/diskless.html)
[iso2usb](https://fedoraproject.org/wiki/How_to_create_and_use_Live_USB)

# Run docker
```bash
docker run --device=/dev/sdX* --privileged -v $(pwd)/test1/:/test1 --rm -it fedora /bin/bash
```

# Prepare env

```{r, engine='bash', count_lines}
cat >> /etc/yum.repos.d/epel.repo <<EOF
[epel]
baseurl=https://dl.fedoraproject.org/pub/epel/7/x86_64/
enabled=1
gpgcheck=0
EOF
```
# Install and build
 Create iso:
```{r, engine='bash', count_lines}
dnf install livecd-tools spin-kickstarts -y
cp -a /usr/share/spin-kickstarts .
cp -ra alexz-live-xfce.ks spin-kickstarts/
pushd spin-kickstarts
livecd-creator --verbose --config=alexz-live-xfce.ks --fslabel=alexz_fedora26 --cache=/test1/cache/live --tmpdir=/test1/temp/ --releasever=26 --compression-type=lz4
popd
# Convert iso to pxe:
livecd-iso-to-pxeboot spin-kickstarts/alexz_fedora26.iso
```
# Write 2 usb:
```{r, engine='bash', count_lines}
 livecd-iso-to-disk --format --reset-mbr --overlay-size-mb 2048 --livedir fedora26_liveos spin-kickstarts/alexz_fedora26.iso /dev/sdX
```


# TODO
 * Use startx to run UI
 * Search for img=>iscsi
