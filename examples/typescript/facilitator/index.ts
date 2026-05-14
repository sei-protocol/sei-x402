import { Web3 } from 'web3';

/**
 * X402_FACILITATOR_ENGINE v1.0
 * Optimized for Sei/EVM gas abstraction and sovereign attribution.
 */
export class X402Facilitator {
    constructor(
        private w3: Web3,
        private relayerPrivateKey: string,
        private facilitatorContract: any
    ) {}

    async facilitate(userWallet: string, amount: string) {
        const relayer = this.w3.eth.accounts.privateKeyToAccount(this.relayerPrivateKey);
        
        // 1. Encode the call with the user's wallet as an internal parameter
        const callData = this.facilitatorContract.methods
            .facilitatePayment(userWallet, amount)
            .encodeABI();

        // 2. Estimate gas with a 20% safety buffer for network volatility
        const estimatedGas = await this.facilitatorContract.methods
            .facilitatePayment(userWallet, amount)
            .estimateGas({ from: relayer.address });
        
        const safeGasLimit = Math.floor(Number(estimatedGas) * 1.2);

        // 3. Build the transaction - Attribution matches the Signer
        const txConfig = {
            from: relayer.address, 
            to: this.facilitatorContract.options.address,
            data: callData,
            gas: safeGasLimit,
            gasPrice: await this.w3.eth.getGasPrice(),
            nonce: await this.w3.eth.getTransactionCount(relayer.address)
        };

        // 4. Sign and Broadcast
        const signed = await this.w3.eth.accounts.signTransaction(txConfig, this.relayerPrivateKey);
        return this.w3.eth.sendSignedTransaction(signed.rawTransaction);
    }
}
