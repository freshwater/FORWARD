
set -e

PORT=8888

PWD_=$PWD
cd $(dirname $0)

# TAG=tag$RANDOM
TAG=forward-jupyter
docker build . --tag $TAG && docker run --rm --publish $PORT:8888 --mount type=bind,src="$PWD_",dst=/workfolder $TAG jupyter notebook --ip=0.0.0.0 --allow-root
