from securesystemslib.interface import (generate_and_write_rsa_keypair,
    import_rsa_privatekey_from_file)
from in_toto.models.layout import Layout, Step, Inspection
from in_toto.models.metadata import Metablock

# Generate key pair for project owner, which will be used to sign
# the project layout. The public key will be used for final product
# verification.
owner_path = generate_and_write_rsa_keypair(filepath="owner")
owner_key = import_rsa_privatekey_from_file(owner_path)

# Generate key pair for developer functionary. There may be any number of
# developers working on a project; for simplicity's sake, we consider the
# case of only one developer. A developer is authorized to make changes to
# source code as well run git commands.
developer_path = generate_and_write_rsa_keypair(filepath="developer")
build_push_path = generate_and_write_rsa_keypair(filepath="build_push")

# Start with an empty layout
layout = Layout()

# Add developer and build & push functionaries' public keys to layout
developer_pubkey = layout.add_functionary_key_from_path(developer_path + ".pub")
build_push_pubkey = layout.add_functionary_key_from_path(build_push_path + ".pub")

# Set an expiration date to layout
layout.set_relative_expiration(months=4)

# Define develop step in software supply chain
step_develop = Step(name="develop")
step_develop.pubkeys = [developer_pubkey["keyid"]]

step_build_push = Step(name="build_push")
step_build_push.pubkeys = [build_push_pubkey["keyid"]]

step_develop.add_product_rule_from_string("ALLOW hello_world/hello_enclave.cc")
step_develop.add_product_rule_from_string("DISALLOW *")

step_build_push.set_expected_command_from_string("executor --skip-tls-verify --dockerfile=Dockerfile \
        --destination=misaelvf2/cloud-sec --context=/workspace/docker-source/hybrid --build-arg=BASE=alpine:3")

inspection = Inspection(name="untar")

inspection.set_run_from_string("tar xzf hello_world.tar.gz")

layout.steps = [step_develop, step_build_push]
layout.inspect = [inspection]

metablock = Metablock(signed=layout)
metablock.sign(owner_key)
metablock.dump("root.layout")