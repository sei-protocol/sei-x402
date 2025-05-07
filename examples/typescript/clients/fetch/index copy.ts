// Install with: npm install x402-fetch

import { privateKeyToAccount } from "viem/accounts";
import { wrapFetchWithPayment } from "x402-fetch";

// Wrap fetch using the user's wallet to make payments
const account = privateKeyToAccount("0x1234...");
const fetchWithPayment = wrapFetchWithPayment(fetch, account);

// Make API requests with automatic payment handling
try {
  const response = await fetchWithPayment("https://api.example.com/premium-data", {
    method: "GET",
  });
  console.log(response.body) // The premium data
} catch (error) {
  console.error('Payment failed', error);
}
