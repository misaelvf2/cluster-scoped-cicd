from securesystemslib.interface import (generate_and_write_rsa_keypair,
    import_rsa_privatekey_from_file)
from in_toto.models.layout import Layout, Step, Inspection
from in_toto.models.metadata import Metablock

# Generate owner RSA key pair. The owner's private key is used to sign the layout,
# and the public key will then be used during product verification.
owner_path = generate_and_write_rsa_keypair(filepath="owner")
owner_key = import_rsa_privatekey_from_file(owner_path)

# Generate developer RSA key pair. The developer is allowed to make changes to source code,
# and run git commands.
developer_path = generate_and_write_rsa_keypair(filepath="developer")

# Generate build and push Service Account RSA key pair. The build and push Service Account
# is the identity assumed by the Pod corresponding to the build and push task
# in the CI/CD pipeline.
build_and_push_path = generate_and_write_rsa_keypair(filepath="build_and_push")

# Create an empty layout
layout = Layout()

# Add the developer and build & push functionary public keys to the layout.
developer_pubkey = layout.add_functionary_key_from_path(developer_path + ".pub")
build_and_push_pubkey = layout.add_functionary_key_from_path(build_and_push_path + ".pub")

# Set expiration date so that the layout will expire in 4 months from now.
layout.set_relative_expiration(months=4)

# Create layout steps
# First step is for developer to clone the repository.
step_clone = Step(name="clone")
step_clone.pubkeys = [developer_pubkey["keyid"]]

# Set the command that is expected to be run for this step.
step_clone.set_expected_command_from_string(
    "git clone https://github.com/misaelvf2/cluster-scoped-cicd.git")

# Specify rules for files expected to be created as result of this step.
step_clone.add_product_rule_from_string("CREATE cluster-scoped-cicd/bazel-test/test/BUILD")
step_clone.add_product_rule_from_string("CREATE cluster-scoped-cicd/bazel-test/test/hello-world.cc")
step_clone.add_product_rule_from_string("DISALLOW cluster-scoped-cicd/bazel-test/test/*")

# Developer may carry out any number of commands when modifying source code.
# These will be captured with the 'in-toto-record' command.
step_modify = Step(name="modify")
step_modify.pubkeys = [developer_pubkey["keyid"]]

# Specify rules for files expected to be passed as input to this step.
# Here we specify that the developer should be operating on the files
# that were the product of the previous 'clone' step.
step_modify.add_material_rule_from_string(
    "MATCH cluster-scoped-cicd/bazel-test/test/* WITH PRODUCTS FROM clone")
step_modify.add_material_rule_from_string("DISALLOW cluster-scoped-cicd/bazel-test/test/*")

# Specify rules for files expected to be created as result of this step.
# Files will be modified versions of files that were the product of the 'clone' step.
step_modify.add_product_rule_from_string("ALLOW cluster-scoped-cicd/bazel-test/test/BUILD")
step_modify.add_product_rule_from_string("ALLOW cluster-scoped-cicd/bazel-test/test/hello-world.cc")
step_modify.add_product_rule_from_string("DISALLOW cluster-scoped-cicd/bazel-test/test/*")

# The build & push Service Account will carry out the build & push
# task in the pipeline, which will begin with the "build and push" step.
step_build_and_push = Step(name="build_and_push")
step_build_and_push.pubkeys = [build_and_push_pubkey["keyid"]]

# Expected command is the Kaniko executor, with given flags.
step_build_and_push.set_expected_command_from_string("executor --skip-tls-verify --dockerfile=Dockerfile \
        --destination=misaelvf2/test-hello-world --context=/workspace/docker-source/ --build-arg=BASE=alpine:3")

# Expected materials are products from the 'modify' step.
step_build_and_push.add_material_rule_from_string(
    "MATCH cluster-scoped-cicd/bazel-test/test/* WITH PRODUCTS FROM modify")
step_build_and_push.add_material_rule_from_string("DISALLOW cluster-scoped-cicd/bazel-test/test/*")

# No expected products from this step.
step_build_and_push.add_product_rule_from_string("DISALLOW asylo-hello-world/hello_world/*")

# Build and push will package source code into tar file.
step_package = Step(name="package")
step_package.pubkeys = [build_and_push_pubkey["keyid"]]

step_package.set_expected_command_from_string(
    "tar --exclude '.git' -zcvf bazel-test.tar.gz bazel-test")

step_package.add_material_rule_from_string("MATCH cluster-scoped-cicd/bazel-test/test/* WITH PRODUCTS FROM modify")
step_package.add_material_rule_from_string("DISALLOW cluster-scoped-cicd/bazel-test/test/*")

step_package.add_product_rule_from_string("CREATE bazel-test.tar.gz")
step_package.add_product_rule_from_string("DISALLOW *")

# Create inspection
# Need to untar file as first step in inspection.
inspection = Inspection(name="untar")

inspection.set_run_from_string("tar xzf bazel-test.tar.gz")

# Material should match product from 'package' step.
inspection.add_material_rule_from_string(
    "MATCH bazel-test.tar.gz WITH PRODUCTS FROM package")

# Product should match product from 'modify' step.
inspection.add_product_rule_from_string(
    "MATCH cluster-scoped-cicd/bazel-test/test/* WITH PRODUCTS FROM modify")

# Add steps and inspections to layout
layout.steps = [step_clone, step_modify, step_package]
layout.inspect = [inspection]

metablock = Metablock(signed=layout)
metablock.sign(owner_key)
metablock.dump("root.layout")