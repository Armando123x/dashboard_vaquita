FROM python:3.10

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY requirements.txt .
# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# running migrations
#RUN python manage.py migrate


COPY install.sh .
RUN chmod +x install.sh
RUN ./install.sh


# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "core.wsgi"]
