FROM ubuntu:xenial
RUN apt-get update && apt-get install -y python-flask python-yaml python-pbr python-setuptools python-pymongo && \
    apt-get install -y apache2 libapache2-mod-wsgi && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
ADD dist/*gz /srv
RUN cd /srv/muds-* && python setup.py install && cd / && rm -rf /srv/muds*
RUN rm /etc/apache2/sites-enabled/*
ADD contrib/apache-default.conf /etc/apache2/sites-enabled/
EXPOSE 80
CMD apache2ctl -DFOREGROUND
