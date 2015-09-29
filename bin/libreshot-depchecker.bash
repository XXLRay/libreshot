
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
echo "ffmpeg/avconv Version"
echo "------"
ffmpeg -version
avconv -version
echo ""
echo "openshot Version"
echo "------"
dpkg-query -W openshot
echo ""
echo "ffmpeg/avconv Version"
echo "------"
dpkg-query -W ffmpeg
dpkg-query -W libav-tools
echo ""
echo "melt / mlt Version"
echo "------"
melt --version |grep melt
echo ""
echo "MLT libraries"
echo "------"
dpkg -l | grep libmlt
echo ""
echo "libav libraries"
echo "------"
dpkg -l |grep libav |grep -v Avahi
echo "------"
echo "Blender version"
echo "------"
blender --version |grep Blender
echo "------"
echo "frei0r plugins"
echo "------"
dpkg -l |grep frei0r
echo "------"
echo "available source packages"
echo ""
echo "------"
dpkg -l | grep -- "-dev"
