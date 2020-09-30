
set -e

PORT=80

PWD_=$PWD
cd $(dirname $0)

# TAG=tag$RANDOM
TAG=forward-interface
docker build . --tag $TAG > /dev/null && docker run --rm --publish $PORT:80 --mount type=bind,src="$PWD_",dst=/workfolder $TAG python3 -u server.py
