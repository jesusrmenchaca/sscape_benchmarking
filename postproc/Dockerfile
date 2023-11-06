# COPYRIGHT

FROM ubuntu:22.04
ARG USERNAME=user
ARG UID=1000
ARG GID=1000

env DEBIAN_FRONTEND=noninteractive
RUN : \
    ; apt update \
    ; apt install texlive-latex-extra -y\
    ; apt-get install -y inkscape \
    ;

RUN : \
    ; apt-get install -y python-is-python3 \
      python3-pip \
    ; pip install pygal \
    ;

RUN : \
    ; groupadd -g ${GID} -o ${USERNAME} \
    ; useradd -m -u ${UID} -g ${GID} ${USERNAME} -G users \
    ;

USER ${USERNAME}

