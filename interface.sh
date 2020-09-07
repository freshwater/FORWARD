
set -e

PORT=8888

PWD_=$PWD
cd $(dirname $0)

TAG=tag$RANDOM
docker build . --tag $TAG && docker run --rm --publish 80:80 --mount type=bind,src="$PWD_",dst=/workfolder $TAG python3 -u server.py
docker rmi $TAG > /dev/null