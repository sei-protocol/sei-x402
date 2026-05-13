# sovereign_withdraw.py
# End-to-end x402 claim + withdraw (NO API KEYS)

# sovereign_withdraw.py
# End-to-end x402 claim + withdraw (NO API KEYS)

import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

from x402.claims.settle_client import load_settlements
from x402.x402_types import Settlement

from eth_account import Account
from web3 import Web3

RPC = "https://mainnet.base.org"  # public, permissionless
CLAIMS_FILE = "./settlements.json"
PRIVATE_KEY_FILE = "./sovereign.key"  # OFFLINE KEY FILE

def load_private_key():
    with open(PRIVATE_KEY_FILE) as f:
        return f.read().strip()

def aggregate(settlements):
    total = 0
    for s in settlements:
        total += int(s.amount)
    return total

def main():
    print("🔎 Loading settlements…")
    settlements = load_settlements()
    if not settlements:
        print("No settlements found.")
        return

    total = aggregate(settlements)
    print(f"💰 Total claimable: {Web3.from_wei(total, 'ether')} ETH")

    w3 = Web3(Web3.HTTPProvider(RPC))
    acct = Account.from_key(load_private_key())

    tx = {
        "to": acct.address,   # self-withdraw (can change)
        "value": total,
        "gas": 21000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "chainId": 8453,  # Base mainnet
    }

    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    print("🚀 Withdrawal sent!")
    print("TX:", tx_hash.hex())

if __name__ == "__main__":
    main()
