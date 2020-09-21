
set -e

PWD_=$PWD
cd $(dirname $0)

# TAG=tag$RANDOM
TAG=forward-shell
docker build . --tag $TAG && docker run --rm --interactive --tty --mount type=bind,src="$PWD_",dst=/workfolder $TAG bash
