keytype: Asymmetric, Sign and verify, ECC_NIST_P256
signature_algorithm: ECDSA_SHA_256


the keytype should match above.   Tags are limited to 255 chars, so we need to use short signatures that fit into tags.  since these are not "High security" tags for any type of sensitive info, the keys and algos listed should be completely fine.


dynamodb table
name: ec2_signatures
primary key: instance_id