# Pandas and Numpy need to be compiled with standard C stuff,
# that is not compatible with Alpine.for that need to use the standard python image

FROM python:3.7

WORKDIR /code

COPY * /code/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
