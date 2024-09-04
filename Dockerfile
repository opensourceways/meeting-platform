FROM openeuler/openeuler:22.03

ARG user=meetingplatform
ARG group=meetingplatform
ARG uid=1000
ARG gid=1000


# install 
RUN yum install -y shadow wget git openssl openssl-devel tzdata python3-devel mariadb-devel python3-pip libXext  \
    libjpeg xorg-x11-fonts-75dpi xorg-x11-fonts-Type1 gcc 
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -d /home/meetingplatform/ -s /sbin/nologin -m ${user}

# 1.copy
COPY ./meeting_platform /home/meetingplatform/meeting-platform
COPY ./manage.py /home/meetingplatform/meeting-platform
COPY ./docker-entrypoint.sh /home/meetingplatform/meeting-platform
COPY ./deploy/production/uwsgi.ini /home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini
COPY ./deploy/fonts/simsun.ttc /usr/share/fonts/simsun.ttc
COPY ./requirements.txt /home/meetingplatform/meeting-platform

# 2.install

RUN pip3 install -r /home/meetingplatform/meeting-platform/requirements.txt && rm -rf /home/meetingplatform/meeting-platform/requirements.txt
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.centos8.x86_64.rpm && \
    rpm -i wkhtmltox-0.12.6-1.centos8.x86_64.rpm && \
    rm -f wkhtmltox-0.12.6-1.centos8.x86_64.rpm

# 3.clean

RUN yum remove -y gcc python3-pip procps-ng
RUN rm -rf /usr/bin/kill
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN chmod -R 550 /home/meetingplatform/meeting-platform/ && \
    chown -R ${user}:${group} /home/meetingplatform/meeting-platform/
RUN chmod 550 /home/meetingplatform/meeting-platform/manage.py && \
    chown ${user}:${group} /home/meetingplatform/meeting-platform/manage.py
RUN chmod 550 /home/meetingplatform/meeting-platform/docker-entrypoint.sh && \
    chown ${user}:${group} /home/meetingplatform/meeting-platform/docker-entrypoint.sh
RUN chmod 550 /usr/share/fonts/simsun.ttc && chown ${user}:${group} /usr/share/fonts/simsun.ttc
RUN mkdir -p /home/meetingplatform/meeting-platform/deploy/static &&  \
    chmod -R 750 /home/meetingplatform/meeting-platform/deploy &&  \
    chown -R ${user}:${group} /home/meetingplatform/meeting-platform/deploy
RUN echo > /etc/issue && echo > /etc/issue.net && echo > /etc/motd
RUN sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/' /etc/login.defs
RUN echo 'set +o history' >> /root/.bashrc
RUN rm -rf /tmp/*
RUN history -c && echo "set +o history" >> /home/meetingplatform/.bashrc  && echo "umask 027" >> /home/meetingplatform/.bashrc && source /home/meetingplatform/.bashrc

# 4.Run server
WORKDIR /home/meetingplatform/meeting-platform
ENV LANG=en_US.UTF-8
USER ${uid}:${gid}

ENTRYPOINT ["/home/meetingplatform/meeting-platform/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini"]
EXPOSE 8080
