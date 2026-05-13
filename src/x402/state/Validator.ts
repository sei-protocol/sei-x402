import crypto from "crypto";

export class Validator {
  // Simple HMAC or Hash-based validation for the Sovereign Agent
  static verify(payment: any, signature: string, secret: string): boolean {
    const expected = crypto
      .createHmac("sha256", secret)
      .update(payment.id)
      .digest("hex");
    return expected === signature;
  }
}
