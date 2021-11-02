FROM alpine:latest
WORKDIR /root
ARG VER="2.32.0"
ARG TARBALL=gobgp_${VER}_linux_amd64
RUN wget https://github.com/osrg/gobgp/releases/download/v${VER}/${TARBALL}.tar.gz
RUN tar xzf ${TARBALL}.tar.gz
RUN rm ${TARBALL}.tar.gz
COPY speaker.sh ./
CMD ["./speaker.sh"]
