import { CdpClient } from "@coinbase/cdp-sdk";
import axios from "axios";
import { config } from "dotenv";
import { toAccount } from "viem/accounts";
import { decodeXPaymentResponse, withPaymentInterceptor } from "x402-axios";

config();

const baseURL = process.env.RESOURCE_SERVER_URL as string; // e.g. https://example.com
const endpointPath = process.env.ENDPOINT_PATH as string; // e.g. /weather
const cdpApiKeyId = process.env.CDP_API_KEY_ID as string;
const cdpApiKeySecret = process.env.CDP_API_KEY_SECRET as string;

if (!baseURL || !endpointPath || !cdpApiKeyId || !cdpApiKeySecret) {
  console.error(
    "Missing required environment variables. Go to https://cdp.coinbase.com/ to create an API key.",
  );
  process.exit(1);
}

const cdp = new CdpClient();

// putting in main so we can use await on the account creation
/**
 *
 */
async function main() {
  try {
    console.log("Creating CDP account...");
    const evmServerAccount = await cdp.evm.getAccount({
      name: "your-existing-account",
    });
    // TODO: Fix typings
    const account = toAccount(evmServerAccount as any);
    const api = withPaymentInterceptor(
      axios.create({
        baseURL,
      }),
      account as any,
    );

    const response = await api.get(endpointPath);

    console.log("\n=== Response Details ===");
    console.log("Status:", response.status);
    console.log("Headers:", response.headers);
    console.log("Data:", response.data);

    if (response.headers["x-payment-response"]) {
      const paymentResponse = decodeXPaymentResponse(response.headers["x-payment-response"]);
      console.log("\n=== Payment Response ===");
      console.log(paymentResponse);
    } else {
      console.log("\nNo x-payment-response header found");
    }
  } catch (error: any) {
    console.error("\n=== Error Details ===");
    if (error.response) {
      // The request was made and the server responded with a status code
      console.error("Response Status:", error.response.status);
      console.error("Response Headers:", error.response.headers);
      console.error("Response Data:", error.response.data);
    } else if (error.request) {
      // The request was made but no response was received
      console.error("No response received. Request details:", error.request);
    } else {
      // Something happened in setting up the request
      console.error("Error setting up request:", error.message);
    }
    console.error("\nFull error:", error);
  }
}

main().catch(console.error);
