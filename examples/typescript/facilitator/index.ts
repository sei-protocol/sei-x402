import { Web3 } from 'web3';

export interface FacilitatorConfig {
    rpcUrl: string;
    relayerPrivateKey: string;
    contractAddress: string;
    abi: any;
}

export class X402Facilitator {
    private w3: Web3;
    private relayerAccount: any;
    private contract: any;

    constructor(config: FacilitatorConfig) {
        this.w3 = new Web3(config.rpcUrl);
        this.relayerAccount = this.w3.eth.accounts.privateKeyToAccount(config.relayerPrivateKey);
        this.contract = new this.w3.eth.Contract(config.abi, config.contractAddress);
    }

    async facilitatePayment(userWallet: string, amount: string) {
        const method = this.contract.methods.facilitatePayment(userWallet, amount);
        
        const [gasPrice, nonce, estimate] = await Promise.all([
            this.w3.eth.getGasPrice(),
            this.w3.eth.getTransactionCount(this.relayerAccount.address),
            method.estimateGas({ from: this.relayerAccount.address })
        ]);

        const tx = {
            from: this.relayerAccount.address,
            to: this.contract.options.address,
            data: method.encodeABI(),
            gas: Math.floor(Number(estimate) * 1.15),
            gasPrice: gasPrice,
            nonce: nonce
        };

        const signed = await this.w3.eth.accounts.signTransaction(tx, this.relayerAccount.privateKey);
        return await this.w3.eth.sendSignedTransaction(signed.rawTransaction);
    }
}
