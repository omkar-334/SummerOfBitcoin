from binascii import hexlify, unhexlify
from hashlib import sha256

import ecdsa
from bitcoinlib.keys import Key
from bitcoinrpc.authproxy import AuthServiceProxy

RPC_URL = "http://alice:password@127.0.0.1:18443"
PRIVATE_KEY_1 = "39dc0a9f0b185a2ee56349691f34716e6e0cda06a7f9707742ac113c4e2317bf"
PRIVATE_KEY_2 = "5077ccd9c558b7d04a81920d38aa11b4a9f9de3b23fab45c3ef28039920fdd6d"


PRIVATE_KEY_1_WIF = Key(PRIVATE_KEY_1).wif()
PRIVATE_KEY_2_WIF = Key(PRIVATE_KEY_2).wif()


REDEEM_SCRIPT_ASM = (
    "OP_2 032ff8c5df0bc00fe1ac2319c3b8070d6d1e04cfbf4fedda499ae7b775185ad53b 039bbc8d24f89e5bc44c5b0d1980d6658316a6b2440023117c3c03a4975b04dd56 OP_2 OP_CHECKMULTISIG"
)
REDEEM_SCRIPT_HEX = "5221032ff8c5df0bc00fe1ac2319c3b8070d6d1e04cfbf4fedda499ae7b775185ad53b21039bbc8d24f89e5bc44c5b0d1980d6658316a6b2440023117c3c03a4975b04dd5652ae"


def private_to_public(private_key_hex):
    private_key_bytes = unhexlify(private_key_hex)
    sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    public_key = b"\x02" + vk.to_string()[:32] if vk.to_string()[32] < 128 else b"\x03" + vk.to_string()[:32]
    return hexlify(public_key).decode()


PUBLIC_KEY_1 = private_to_public(PRIVATE_KEY_1)
PUBLIC_KEY_2 = private_to_public(PRIVATE_KEY_2)


transaction = {
    "hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "index": 0,
    "sequence": 0xFFFFFFFF,
    "value": 0.001,
    # "address": "325UUecEQuyrTd28Xs2hvAxdAjHM7XzqVF",
    "address": "2MzkHLKDFR5LthUbkWA5iyck3fgGF4jQiqG",
    "locktime": 0,
}


def sign_tx(privkey, sighash):
    sk = ecdsa.SigningKey.from_string(unhexlify(privkey), curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    signature = sk.sign_deterministic(unhexlify(sighash), hashfunc=sha256)
    return hexlify(signature).decode() + "01"  # Append SIGHASH_ALL (01)


def main():
    rpc_client = AuthServiceProxy(RPC_URL)

    redeem_script = unhexlify(REDEEM_SCRIPT_HEX)
    p2wsh_script = sha256(redeem_script).digest()
    # p2sh_p2wsh_address = rpc_client.addmultisigaddress(2, [PUBLIC_KEY_1, PUBLIC_KEY_2])["address"]
    p2sh_p2wsh_script = b"\x00\x20" + p2wsh_script  # P2WSH scriptPubKey
    p2sh_p2wsh_address = rpc_client.createmultisig(2, [PUBLIC_KEY_1, PUBLIC_KEY_2])["address"]

    raw_tx = rpc_client.createrawtransaction(
        [{"txid": transaction["hash"], "vout": transaction["index"], "sequence": transaction["sequence"]}],
        {transaction["address"]: transaction["value"]},
    )

    psbt = rpc_client.converttopsbt(raw_tx)
    sighash = sha256(sha256(unhexlify(raw_tx)).digest()).hexdigest()

    # decoded_tx = rpc_client.decoderawtransaction(raw_tx)
    # sighash = rpc_client.getrawtransaction(transaction["hash"], True)["vout"][transaction["index"]]["scriptPubKey"]["hex"]

    sig1 = sign_tx(PRIVATE_KEY_1, sighash)
    sig2 = sign_tx(PRIVATE_KEY_2, sighash)

    witness = ["", sig1, sig2, REDEEM_SCRIPT_HEX]

    signed_tx = rpc_client.signrawtransactionwithkey(
        raw_tx,
        [PRIVATE_KEY_1_WIF, PRIVATE_KEY_2_WIF],
        [{"txid": transaction["hash"], "vout": transaction["index"], "scriptPubKey": p2sh_p2wsh_script.hex(), "redeemScript": REDEEM_SCRIPT_HEX}],
    )
    if not signed_tx["complete"]:
        raise Exception("Transaction signing failed!")

    final_tx = signed_tx["hex"]

    # final_tx = rpc_client.finalizepsbt(raw_tx)

    with open("out.txt", "w") as f:
        f.write(final_tx)


if __name__ == "__main__":
    main()
