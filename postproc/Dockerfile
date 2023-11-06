# COPYRIGHT

FROM ubuntu:22.04

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
    ; useradd -m user -G users \
    ;

USER user

