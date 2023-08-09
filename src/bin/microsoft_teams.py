#/usr/bin/env bash

# Absolute path to this script. /home/user/bin/foo.sh
SCRIPT=$(readlink -f $0)
# Absolute path this script is in. /home/user/bin
SCRIPTPATH=`dirname $SCRIPT`
asset_path=$(dirname -- ${SCRIPTPATH})
echo "$(dirname -- ${SCRIPTPATH})"

# Prepend relative library path to PYTHONPATH
# to ensure modules are found.
export PYTHONPATH="${asset_path}/lib:$PYTHONPATH"
export PYTHONPATH="${asset_path}/lib"
export PYTHONPATH="${asset_path}/lib/pymsteams"
export PYTHONPATH="${asset_path}/lib/requests"
export PYTHONPATH="${asset_path}/lib/urllib3"

echo "PYTHONPATH---------="${asset_path}/lib:$PYTHONPATH""
program="${0##*/}"
exec "${asset_path}/libexec/${program}" "$@"