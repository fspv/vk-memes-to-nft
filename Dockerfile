FROM ubuntu:jammy

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get install -y git
RUN apt-get install -y python3-virtualenv
RUN apt-get install -y curl wget
RUN apt-get install -y libssl-dev
RUN apt-get install -y libsqlite3-dev
RUN apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install python 3.9.11
RUN git clone https://github.com/pyenv/pyenv.git /root/.pyenv
RUN /root/.pyenv/bin/pyenv install 3.9.11
RUN  /root/.pyenv/bin/pyenv global 3.9.11
ENV PYTHON_BIN /root/.pyenv/versions/3.9.11/bin/python

# Create python venv
RUN virtualenv -p ${PYTHON_BIN} /root/.venv
RUN . /root/.venv/bin/activate && pip install ipython

# Install OpenSea uploader
RUN mkdir /src
RUN cd /src && git clone https://github.com/maximedrn/opensea-automatic-bulk-upload-and-sale.git
RUN cd /src/opensea-automatic-bulk-upload-and-sale && git checkout 908750e30988f7d01f6bdd41815eff429f37f8ec
RUN . /root/.venv/bin/activate && pip install -r /src/opensea-automatic-bulk-upload-and-sale/requirements.txt
RUN rm -rf /src/opensea-automatic-bulk-upload-and-sale/data/*
RUN add-apt-repository -y ppa:mozillateam/ppa
RUN apt-get update
RUN echo "Package: *\nPin: origin ppa.launchpadcontent.net\nPin-Priority: 995\n" > /etc/apt/preferences.d/firefox.pref
RUN apt-get install -y firefox

# Add data
COPY follower /src/follower
COPY uploader /src/uploader
COPY vk /src/vk
COPY run.sh /src/run.sh
COPY no_captcha.tar.gz /src/no_captcha.tar.gz
RUN . /root/.venv/bin/activate && pip install -r /src/follower/requirements.txt
RUN . /root/.venv/bin/activate && pip install -r /src/uploader/requirements.txt
RUN . /root/.venv/bin/activate && pip install -r /src/vk/requirements.txt
RUN cd /src && tar zxvf no_captcha.tar.gz
RUN mv /src/no_captcha.py /src/opensea-automatic-bulk-upload-and-sale/app/services/solvers/no_captcha.py
