
all:
	docker build \
	    --build-arg http_proxy=$(http_proxy) \
	    --build-arg https_proxy=$(https_proxy) \
	    --build-arg no_proxy=$(no_proxy) \
	    --build-arg USERNAME=$$(whoami) \
	    --build-arg UID=$$(id -u) \
	    --build-arg GID=$$(id -g) \
            -f Dockerfile . -t benchmark:latest
