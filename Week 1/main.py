from bitcoinrpc.authproxy import AuthServiceProxy

# Node access params
RPC_URL = "http://alice:password@127.0.0.1:18443"


def send(rpc, addr, data):
    args = [
        {addr: 100},  # recipient address
        None,  # conf target
        None,
        21,  # fee rate in sats/vb
        None,  # Empty option object
    ]
    send_result = rpc.send("send", args)
    assert send_result["complete"]
    return send_result["txid"]


# this function lists the available wallets
def list_wallet_dir(rpc):
    result = rpc.listwalletdir()
    return [wallet["name"] for wallet in result["wallets"]]


# this function retrieves the wallet if it is available, otherwise creates new wallet and returns it
def get_wallet(rpc, wallet_name="testwall"):
    wallets = list_wallet_dir(rpc)

    if wallet_name not in wallets:
        rpc.createwallet(wallet_name)

    return AuthServiceProxy(f"{RPC_URL}/wallet/{wallet_name}")


# this function mines the given number of bloicks to the given address
def mine(rpc, num_blocks, address):
    return rpc.generatetoaddress(num_blocks, address)


#
def main():
    rpc_client = AuthServiceProxy(RPC_URL)

    # Check connection
    info = rpc_client.getblockchaininfo()
    print(info)

    # Create or load the wallet
    rpc = get_wallet(rpc_client)

    # Generate a new address
    address = rpc.getnewaddress()
    print(f"New Address: {address}")

    # Mine 101 blocks to the new address to activate the wallet with mined coins
    mine(rpc, 101, address)
    print("101 blocks mined")

    # Prepare a transaction to send 100 BTC
    amount = 100
    # check balance first
    balance = rpc.getbalance()

    # create new address to send funds
    recipient_address = rpc.getnewaddress()

    # Send the transaction if balance is sufficient
    if balance < amount:
        raise Exception(f"Insufficient funds! Available: {balance} BTC")
    else:
        txid = rpc.sendtoaddress(recipient_address, amount)
    print(f"Transaction ID: {txid}")

    # Write the txid to out.txt
    with open("out.txt", "w") as f:
        f.write(txid)

    print("Transaction complete!")


if __name__ == "__main__":
    main()

# output
# {'chain': 'regtest', 'blocks': 303, 'headers': 303, 'bestblockhash': '184e4caec8fc46f0749bedce49c09714dbfc23c853214900df98eb8a28ef13ad', 'difficulty': Decimal('4.656542373906925E-10'), 'time': 1740162141, 'mediantime': 1740162140, 'verificationprogress': 1, 'initialblockdownload': False, 'chainwork': '0000000000000000000000000000000000000000000000000000000000000260', 'size_on_disk': 91345, 'pruned': False, 'warnings': ''}

# New Address: bcrt1qrh4jx7skz8gjj0jqyf6zv4anqhlhksxeyvus49
# 101 blocks mined
# Transaction ID: b9f44acfa97e409d2d17df8cc9104dcd52682fbafc1b9118cf6920fc721d6397
# Transaction complete!
