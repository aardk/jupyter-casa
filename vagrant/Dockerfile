FROM penngwyn/jupytercasa:casa-6.5
CMD ["/usr/sbin/sshd", "-D"]
USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get -y upgrade && apt-get clean

# Setup enviroment
RUN apt-get install -y ssh sudo
RUN echo -n 'jupyter:jupyter' | chpasswd
RUN echo 'jupyter ALL = NOPASSWD: ALL' > /etc/sudoers.d/jupyter
RUN chmod 440 /etc/sudoers.d/jupyter
RUN mkdir -p /home/jupyter/.ssh
RUN chmod 700 /home/jupyter/.ssh
RUN echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ==" > /home/jupyter/.ssh/authorized_keys
RUN chmod 600 /home/jupyter/.ssh/authorized_keys
RUN chown -R jupyter:jupyter /home/jupyter/.ssh
RUN sed -i -e 's/Defaults.*requiretty/#&/' /etc/sudoers
RUN sed -i -e 's/\(UsePAM \)yes/\1 no/' /etc/ssh/sshd_config
RUN sed -i -e 's/\#X11UseLocalhost yes/X11UseLocalhost no/' /etc/ssh/sshd_config

RUN mkdir /var/run/sshd
COPY --chown=jupyter:jupyter jupyter_notebook_config.py /home/jupyter/.jupyter
COPY --chown=jupyter:jupyter jupyter_lab_config.py /home/jupyter/.jupyter
