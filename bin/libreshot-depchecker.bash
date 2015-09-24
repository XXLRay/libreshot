#!/bin/bash

echo "Kernel"
echo "------"
uname -a
echo ""
echo "Architecture"
echo "------"
uname -m
echo ""
echo "OS Version"
echo "------"
cat /etc/issue.net
echo ""
echo "ffmpeg Version"
echo "------"
ffmpeg -version
echo ""
echo "openshot Version"
echo "------"
dpkg-query -W openshot
echo ""
echo "ffmpeg Version"
echo "------"
dpkg-query -W ffmpeg
echo ""
echo "melt / mlt Version"
echo "------"
melt --version |grep MLT
echo ""
echo "Version libreria MLT"
echo "------"
dpkg -l | grep libmlt
echo ""
echo "Version libreria libav"
echo "------"
dpkg -l |grep libav
