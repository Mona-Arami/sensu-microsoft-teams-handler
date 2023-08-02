echo $PWD
#/usr/bin/env bash
# Absolute path to this script. /home/user/bin/foo.sh
SCRIPT=$(readlink -f $0)
echo SCRIPT
# Absolute path this script is in. /home/user/bin
SCRIPTPATH=`dirname $SCRIPT`
echo SCRIPTPATH
asset_path=$(dirname -- ${SCRIPTPATH})
echo asset_path
# Prepend relative library path to PYTHONPATH
# to ensure modules are found.
export PYTHONPATH="${asset_path}/lib:$PYTHONPATH"
echo PYTHONPATH
program="${0##*/}"
exec "${asset_path}/libexec/${program}" "$@"
