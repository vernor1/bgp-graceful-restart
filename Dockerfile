FROM python:3 as py-builder
RUN git clone https://github.com/osrg/gobgp.git && \
    cd gobgp && \
    git checkout v2.32.0 && \
    pip install grpcio grpcio-tools && \
    python3 -m grpc_tools.protoc -I./api --python_out=/root --grpc_python_out=/root api/gobgp.proto api/attribute.proto api/capability.proto

FROM debian:latest as app
RUN apt-get update && apt-get install -y procps vim cron tcpdump python3 python3-pip
RUN pip3 install grpcio grpcio-tools
WORKDIR /root
COPY --from=py-builder /root/*.py ./
COPY speaker.py ./
