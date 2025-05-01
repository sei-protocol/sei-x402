# VRF NFT Minting Example (via x402 Payment)

This example demonstrates how a client pays USDC via the `x402` protocol (`exact` scheme) to a custom resource server. This resource server, upon successful payment verification and settlement via a facilitator, then uses its own funds to pay ETH and mint a VRF NFT to the client's address.

Based on the value returned by the VRF result, one of four characters will be selected for the NFT. The NFT and its image can be viewed on [OpenSea](https://testnets.opensea.io/) by connecting to Base Sepolia and searching for the NFT contract address.

## Architecture / How it works.

This example involves three components running concurrently:

1.  **Facilitator (`examples/typescript/facilitator.ts`):** A standard x402 facilitator server responsible for verifying payment signatures (`/verify`) and settling USDC payments (`/settle`) by calling `transferWithAuthorization` on the USDC contract.
2.  **VRF Resource Server (`resource.ts`):** A custom HTTP server (using Hono) that:
    - Exposes a `/request-mint` endpoint.
    - Handles initial requests by responding with `402 Payment Required`, providing the necessary `PaymentDetails` (USDC amount, recipient address, etc.).
    - Receives subsequent requests containing the `X-PAYMENT` header (sent by the client's interceptor).
    - Calls the **Facilitator's** `/verify` endpoint to validate the client's payment authorization.
    - If valid, it extracts the client's address (`from`) from the payment payload.
    - Uses its _own wallet_ (funded with ETH) and `viem` to call `requestNFT(address _recipient)` on the target NFT contract, passing the client's address and the required ETH value.
    - Calls the **Facilitator's** `/settle` endpoint to trigger the actual USDC transfer from the client to the resource server's wallet.
    - Responds to the client with the outcome (including minting and settlement transaction hashes).
3.  **Client (`client.ts`):** A script that:
    - Uses `axios` with the `x402/axios` interceptor. The implementation of this custom interceptor is in `/typescript/packages/x402-axios`.
    - Makes a request to the **Resource Server's** `/request-mint` endpoint.
    - The interceptor automatically handles the `402` response, prompts the client's wallet (via `viem`) to sign the EIP-3009 authorization for the USDC payment, constructs the `X-PAYMENT` header, and retries the request.

## Prerequisites

1. Wallet private key with Base Sepolia Eth and LINK.
2. Base Sepolia RPC URL. You can get this from the [Base Docs](https://docs.base.org/chain/network-information). Currently we use `https://sepolia.base.org/`.

## Setup

1. **Install and Build the Monorepo's Packages:**

   ```bash
   cd ./typescript
   npx pnpm install
   npx pnpm build
   ```

2. **Install and Build Example Dependencies:**

   ```bash
   cd ../examples/typescript
   npx pnpm install
   npx pnpm build
   ```

3. **Install the Chainlink x402 VRF NFT Project's Dependencies:**

   ```bash
   cd clients/vrfnft
   pnpm install
   ```

4. **Environment Variables (`example/.env`):** Create a `.env` file in the `example` directory with the following variables (replace placeholder values):

   ```dotenv
   # Wallet that pays the USDC (needs USDC and ETH for gas)
   PRIVATE_KEY=0xYOUR_CLIENT_PRIVATE_KEY

   # HTTP RPC endpoint for the blockchain network (e.g., Base Sepolia)
   # Must be accessible by all components
   PROVIDER_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
   ```

## Running the Example

You need three separate terminals, all navigated to the `example` directory.

1.  **Terminal 1: Start Facilitator:**

    Start a new terminal instance

    ```bash
    cd examples/typescript/facilitator
    cp .env-local .env
    ```

    Fill in the value for `PRIVATE_KEY=` in the `.env` file (make sure it has the `0x` prefix) then run:

    ```bash
    pnpm dev
    ```

    If successful, your terminal will confirm that the `Server listening at http://localhost:3002`.

2.  **Terminal 2: Start VRF Resource Server:**

    Start a new terminal instance.

    First cd into the right directory with `cd examples/typescript/clients/vrfnft` and then run `cp .env-local .env`.

    Make sure you put fill in the env vars in the .env file inside this directory.

    Then `pnpm run resource`

    If successful, you will see information printed to your console along the lines of:

    ```
    VRF NFT Resource Server running on port 4023
        - Resource Server Wallet: 0x208AA722Aca42399eaC5192EE778e4D42f4E5De3
        - NFT Contract: 0xcD8841f9a8Dbc483386fD80ab6E9FD9656Da39A2
        - Payment Required: 50000 wei USDC (0x036CbD53842c5426634e7929541eC2318f3dCF7e) to 0x87002564F1C7b8F51e96CA7D545e43402BF0b4Ab
        - Facilitator URL: http://localhost:3002

    ```

3.  **Terminal 3: Run VRF Client:**

    Start a new terminal instance

    ```bash
    cd examples/typescript/clients/vrfnft
    pnpm run client
    ```

    If successful you should see information in your terminal that confirms the minting of the randomized NFT (meaning your USDC payment was made and verified) as follows:

    ```
    Client: Requesting NFT mint from http://localhost:4023/request-mint using wallet 0x208AA722Aca42399eaC5192EE778e4D42f4E5De3
    Client: Success! Resource Server Response:
    Status: 200
    Data: {
    "message": "NFT mint request initiated successfully.",
    "nftMintTxHash": "0xeee74e323af3e981e60a6a3299757fa53a0f9fff8409d7df76165e8df38e7bf9"
    }
    check the NFT on testnet.opensea.io, using the NFT Contract's address: '0xcD8841f9a8Dbc483386fD80ab6E9FD9656Da39A2'. You can also check the NFT contract's transactions on Base Sepolia's explorer: https://sepolia.basescan.org/address/0xcD8841f9a8Dbc483386fD80ab6E9FD9656Da39A2.
    ```
