
set -e

PORT=80

PWD_=$PWD
cd $(dirname $0)

MODE=production

TAG=forward-interface-$RANDOM
docker build . --tag $TAG > /dev/null && docker run --env FLASK_ENV=$MODE --rm --publish $PORT:80 --mount type=bind,src="$PWD_",dst=/workfolder $TAG \
    flask run --host=0.0.0.0 --port=80
