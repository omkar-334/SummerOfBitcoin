import binascii
from hashlib import sha256

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Connect to Bitcoin Core
RPC_URL = "http://alice:password@127.0.0.1:18443"
rpc = AuthServiceProxy(RPC_URL)

# Private Keys
PRIV_KEY_1 = "39dc0a9f0b185a2ee56349691f34716e6e0cda06a7f9707742ac113c4e2317bf"
PRIV_KEY_2 = "5077ccd9c558b7d04a81920d38aa11b4a9f9de3b23fab45c3ef28039920fdd6d"

# Public Keys
PUB_KEY_1 = "032ff8c5df0bc00fe1ac2319c3b8070d6d1e04cfbf4fedda499ae7b775185ad53b"
PUB_KEY_2 = "039bbc8d24f89e5bc44c5b0d1980d6658316a6b2440023117c3c03a4975b04dd56"

# Construct the P2SH-P2WSH Redeem Script
redeem_script = f"5221{PUB_KEY_1}21{PUB_KEY_2}52ae"
redeem_script_bin = binascii.unhexlify(redeem_script)

# Generate P2SH Address (Wrapped SegWit)
p2sh_p2wsh_address = rpc.addmultisigaddress(2, [PUB_KEY_1, PUB_KEY_2])

print(f"P2SH-P2WSH Address: {p2sh_p2wsh_address}")

# Import Address (For Watch-Only Use)
try:
    rpc.importmulti([{"scriptPubKey": {"address": p2sh_p2wsh_address}, "redeemscript": redeem_script, "timestamp": "now", "watchonly": True}])
    print("Imported P2SH-P2WSH address into the wallet.")
except JSONRPCException as e:
    print(f"Error importing address: {e}")

# Check UTXOs
utxos = rpc.listunspent(1, 9999999, [p2sh_p2wsh_address])

if not utxos:
    rpc.generatetoaddress(101, rpc.getnewaddress())
    utxos = rpc.listunspent(1, 9999999, [p2sh_p2wsh_address])

# Use the first UTXO
utxo = utxos[0]
txid = utxo["txid"]
vout = utxo["vout"]
amount = utxo["amount"]

# Destination Address
dest_address = rpc.getnewaddress()

# Create Raw Transaction
outputs = {
    dest_address: 0.001,  # Sending 0.001 BTC
    rpc.getrawchangeaddress(): amount - 0.0012,  # Change minus fees
}
raw_tx = rpc.createrawtransaction([{"txid": txid, "vout": vout}], outputs)

# Sign the Transaction with Both Private Keys
signed_tx = rpc.signrawtransactionwithkey(
    raw_tx, [PRIV_KEY_1, PRIV_KEY_2], [{"txid": txid, "vout": vout, "scriptPubKey": utxo["scriptPubKey"], "redeemScript": redeem_script, "amount": amount}]
)

# Broadcast Transaction
if signed_tx["complete"]:
    final_tx_hex = signed_tx["hex"]
    txid = rpc.sendrawtransaction(final_tx_hex)
    print(f"Transaction Broadcasted: {txid}")

    # Save the transaction hex
    with open("out.txt", "w") as f:
        f.write(final_tx_hex)
    print("Transaction hex saved to out.txt")
else:
    print("Transaction signing incomplete. Check keys and UTXO details.")
