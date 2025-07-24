import sys 

sys.dont_write_bytecode = True

from Decrypt import EncryptionSystem

order = {
    "basic_order": [
        "stamp",
        "errs",
        "messages",
        "href",
        "perf",
        "fingerprint_blob",
        "ardata",
        "stack_data",
        "rand",
        "components",
        "proof_spec",
        "tup_"
    ],
    "proof_order": [
        "_location",
        "difficulty",
        "data",
        "_type",
        "fingerprint_type",
        "timeout_value",
        "tup_"
    ],
    "proof_tup": "tup_ae7748639eeb1e4cdf244e3bf70fd06faab12c2d53e96163e02247cc63b84febe1e7e41fbad5bcefc9ed6b4551d9baf7d4be9b9d3dde5f03d241d0fb9edeef5775731ae41e6b51f805bd82edbe6bd128b3e3a912e1c305dbd524",
    "basic_tup": "tup_34c5fc00d40f4a9fd1a8448931c21ab88138c638b816ee34ab8b594f2cd8a0dc24198e973cf2bba60db8ebfae0b948eb952351e2c67ef8c310e69ce56f538c23f835dfd7990f3124f98e42bad88ea022820113e1d5a8a084cba64ecfd9f7eb4ce2cf4f3c61c63889c9bcc5130e5b731b840b4ad04a1164"
}

version = "f21494094c3c0dd7bcff14aba835d5fea0234ef82e9fea2684be17956c94a27e"

shouldSave = True

system = EncryptionSystem(version, order, shouldSave)
