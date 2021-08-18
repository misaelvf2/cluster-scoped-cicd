FROM gcr.io/asylo-framework/asylo

WORKDIR /workdir

COPY . /workdir

RUN apt update

# RUN apt install apt-transport-https curl gnupg -y

# RUN curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg

# RUN mv bazel.gpg /etc/apt/trusted.gpg.d/

# RUN echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list

# RUN apt install bazel -y

RUN ["bazel", "build", "//test:hello-world"]

ENTRYPOINT ["bazel-bin/test/hello-world"]

# ENTRYPOINT ["./bazel-bin/hello_world/hello_world_sgx_sim"]
# CMD ["World!"]
