sudo apt-get -y install fbi 

#we need our current directory
_mydir="`pwd`"

cd /etc
# Patch the boot file rc.local
if patch -p1 --dry-run -i < _mydir/rc.local.patch > /dev/null ; then
	patch -p1 -i rc.local.patch
fi
