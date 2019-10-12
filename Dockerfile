FROM python:3.7

RUN mkdir -p /traceflow/vars

WORKDIR /traceflow/

ADD README.md .
ADD setup.py .
ADD requirements.txt .
ADD traceflow /traceflow/traceflow
ADD vars /traceflow/vars
ADD docker/entrypoint.sh .

RUN pip install -r requirements.txt

RUN python setup.py bdist_wheel
RUN pip install dist/traceflow*any.whl

EXPOSE 8081/tcp

ENTRYPOINT ["sh", "entrypoint.sh"]
