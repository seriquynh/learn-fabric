FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get update && \
    apt-get install -y sudo pip ssh fabric python3-typer && \
    apt-get clean && \
    apt-get autoremove -y &&  \
    rm -rf /tmp/* /var/tmp/* && \
    rm -rf /var/cache/apt/*

RUN useradd -m -s /usr/bin/bash fabric

RUN usermod -aG sudo fabric

RUN echo 'fabric ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/fabric

RUN mkdir /home/fabric/.ssh

RUN chown fabric:fabric -R /home/fabric/.ssh

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /home/fabric

USER fabric

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
