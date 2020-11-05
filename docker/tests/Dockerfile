FROM python:3.7-alpine

RUN mkdir -p /traceflow/var

WORKDIR /traceflow/

ADD . /traceflow/

RUN pip install -r requirements.txt
RUN pip install -r requirements-build.txt

RUN python setup.py bdist_wheel
RUN pip install dist/traceflow*any.whl

EXPOSE 8081/tcp

ENTRYPOINT ["python", "-m", "pytest"]
