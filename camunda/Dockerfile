FROM maven:3.6.3-adoptopenjdk-14 AS JAVA_TOOLCHAIN
WORKDIR /tmp/

# pre-populate maven cache
RUN \
    curl -LO https://gitlab.com/atsoukka/robot-rpa-playground/-/archive/master/robot-rpa-playground.tar.gz; \
    tar xzvf robot-rpa-playground.tar.gz; \
    cd robot-*/camunda; \
    mvn package

# build with current
RUN \
    mkdir -p /tmp/build; \
    cd /tmp/build
ADD app ./app/
ADD pom.xml ./
RUN mvn package

FROM alpine:3.12.1
ENV DEBUG=false
ENV JAVA_OPTS="-Xmx2048m -XX:MaxMetaspaceSize=256m"
ENV TZ UTC
ENV WAIT_FOR_TIMEOUT 30
RUN apk add --no-cache \
        bash \
        ca-certificates \
        curl \
        openjdk11-jre-headless \
        tzdata \
        tini \
        xmlstarlet
RUN addgroup -g 1000 -S camunda && \
    adduser -u 1000 -S camunda -G camunda -h /camunda -s /bin/bash -D camunda
WORKDIR /camunda
USER camunda

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["./docker-entrypoint.sh"]

COPY --chown=camunda:camunda docker-entrypoint.sh /camunda/docker-entrypoint.sh
COPY --chown=camunda:camunda --from=JAVA_TOOLCHAIN /tmp/app/target/*.jar /camunda/camunda.jar
