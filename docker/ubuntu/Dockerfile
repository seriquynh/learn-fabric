# Use an official Ubuntu base image
FROM ubuntu:24.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV SSH_USERNAME="vagrant"
ENV SSHD_CONFIG_ADDITIONAL=""

# Install OpenSSH server, clean up, create directories, set permissions, and configure SSH
RUN apt-get update \
    && apt-get install -y iproute2 iputils-ping openssh-server telnet sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && mkdir -p /run/sshd \
    && chmod 755 /run/sshd \
    && if ! id -u "$SSH_USERNAME" > /dev/null 2>&1; then useradd -ms /bin/bash "$SSH_USERNAME"; fi \
    && chown -R "$SSH_USERNAME":"$SSH_USERNAME" /home/"$SSH_USERNAME" \
    && chmod 755 /home/"$SSH_USERNAME" \
    && mkdir -p /home/"$SSH_USERNAME"/.ssh \
    && chown "$SSH_USERNAME":"$SSH_USERNAME" /home/"$SSH_USERNAME"/.ssh \
    && echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config \
    && echo "PermitRootLogin no" >> /etc/ssh/sshd_config

RUN usermod -aG sudo $SSH_USERNAME && echo "$SSH_USERNAME ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$SSH_USERNAME

# Copy the script to configure the user's password and authorized keys
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose SSH port
EXPOSE 22

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
