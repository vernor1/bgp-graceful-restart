FROM alpine:latest
WORKDIR /root
ARG VER="2.32.0"
ARG TARBALL=gobgp_${VER}_linux_amd64
RUN wget https://github.com/osrg/gobgp/releases/download/v${VER}/${TARBALL}.tar.gz
RUN tar xzf ${TARBALL}.tar.gz
RUN rm ${TARBALL}.tar.gz
COPY gobgpd_reflector.conf.in reflector.sh ./
CMD ["./reflector.sh", "65000", "10.0.0.1", "10.0.0.2"]
