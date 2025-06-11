import time
import secrets
from typing import Dict, Any
from web3 import Web3
from x402.encoding import safe_base64_encode, safe_base64_decode
from x402.types import (
    PaymentPayload,
    ExactPaymentPayload,
    EIP3009Authorization,
    PaymentRequirements,
    UnsupportedSchemeException,
)
from x402.chains import get_chain_id, get_token_name, get_token_version
import json
from eth_account.messages import encode_defunct
import logging

logger = logging.getLogger(__name__)


def create_nonce() -> bytes:
    """Create a random 32-byte nonce for authorization signatures."""
    return secrets.token_bytes(32)


def prepare_payment_header(
    sender_address: str, x402_version: int, payment_requirements: PaymentRequirements
) -> Dict[str, Any]:
    """Prepare an unsigned payment header with sender address, x402 version, and payment requirements."""
    return {
        "sender": sender_address,
        "x402_version": x402_version,
        "payment_requirements": payment_requirements.model_dump(),
    }


def sign_payment_header(
    web3: Web3, payment_requirements: PaymentRequirements, header: dict
) -> str:
    """Sign a payment header using the account's private key."""
    try:
        # Get the authorization object
        auth = header["payload"]["authorization"]
        logger.debug(f"Signing authorization: {auth}")

        # Convert nonce to bytes for signing
        nonce_bytes = bytes.fromhex(auth["nonce"])
        logger.debug(f"Converted nonce to bytes: {nonce_bytes.hex()}")

        # Create the typed data for EIP-712 signing
        typed_data = {
            "types": {
                "TransferWithAuthorization": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "validAfter", "type": "uint256"},
                    {"name": "validBefore", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"},
                ]
            },
            "primaryType": "TransferWithAuthorization",
            "domain": {
                "name": payment_requirements.extra["name"],
                "version": payment_requirements.extra["version"],
                "chainId": int(web3.eth.chain_id),
                "verifyingContract": payment_requirements.asset,
            },
            "message": {
                "from": auth["from"],
                "to": auth["to"],
                "value": int(auth["value"]),
                "validAfter": int(auth["validAfter"]),
                "validBefore": int(auth["validBefore"]),
                "nonce": nonce_bytes,
            },
        }
        logger.debug(f"Typed data for signing: {typed_data}")

        # Get the account's private key
        account = web3.eth.default_account
        if not account:
            raise ValueError("No default account set in Web3 instance")

        # Sign the typed data
        signed_message = web3.eth.account.sign_typed_data(
            private_key=account.key,
            domain_data=typed_data["domain"],
            message_types=typed_data["types"],
            message_data=typed_data["message"],
        )
        signature = signed_message.signature.hex()
        if not signature.startswith("0x"):
            signature = f"0x{signature}"
        logger.debug(f"Generated signature: {signature}")

        # Add signature to header
        header["payload"]["signature"] = signature

        # Add 0x prefix to nonce for the final header
        header["payload"]["authorization"]["nonce"] = f"0x{auth['nonce']}"

        # Encode the header
        encoded = encode_payment(header)
        logger.debug(f"Encoded payment header: {encoded}")
        return encoded
    except Exception as e:
        logger.error(f"Error signing payment header: {e}")
        raise


def encode_payment(payment_payload: Dict[str, Any]) -> str:
    """Encode a payment payload into a base64 string, handling HexBytes and other non-serializable types."""
    from x402.encoding import safe_base64_encode
    from hexbytes import HexBytes

    def default(obj):
        if isinstance(obj, HexBytes):
            return obj.hex()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "hex"):
            return obj.hex()
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    return safe_base64_encode(json.dumps(payment_payload, default=default))


def decode_payment(encoded_payment: str) -> Dict[str, Any]:
    """Decode a base64 encoded payment string back into a PaymentPayload object."""
    from x402.encoding import safe_base64_decode

    return json.loads(safe_base64_decode(encoded_payment))
