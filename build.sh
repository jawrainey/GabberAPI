if [ -z "$1" ]
then
    echo "Pass version, e.g x.y.z"
    exit 1
fi

REGISTRY="gabber/api"
VERSION="$1"

docker build -t "$REGISTRY:$VERSION" -t "$REGISTRY:latest" .
docker push "$REGISTRY:$VERSION"
docker push "$REGISTRY:latest"
