package coinbasefacilitator

import (
	"fmt"

	"github.com/coinbase/cdp-sdk/go/auth"
)

// CreateAuthHeader creates an authorization header for a request to the Coinbase API.
//
// Parameters:
//   - apiKeyId: The api key ID
//   - apiKeySecret: The api key secret
//   - requestHost: The host for the request (e.g. 'https://x402.org/facilitator')
//   - requestPath: The path for the request (e.g. '/verify')
//
// Returns:
//   - The authorization header string and any error that occurred
func CreateAuthHeader(apiKeyId, apiKeySecret, requestHost, requestPath string) (string, error) {
	// Debug print all parameters
	fmt.Printf("\n=== JWT Debug Info ===\n")
	fmt.Printf("KeyID: %s\n", apiKeyId)
	fmt.Printf("KeySecret length: %d\n", len(apiKeySecret))
	fmt.Printf("RequestHost: %s\n", requestHost)
	fmt.Printf("RequestPath: %s\n", requestPath)
	fmt.Printf("RequestMethod: POST\n")

	jwt, err := auth.GenerateJWT(auth.JwtOptions{
		KeyID:         apiKeyId,
		KeySecret:     apiKeySecret,
		RequestMethod: "POST",
		RequestHost:   requestHost,
		RequestPath:   requestPath,
	})
	if err != nil {
		fmt.Printf("JWT Generation Error: %v\n", err)
		return "", err
	}

	bearerToken := "Bearer " + jwt
	fmt.Printf("Generated Bearer Token: %s\n", bearerToken)
	fmt.Printf("=== End JWT Debug Info ===\n\n")

	return bearerToken, nil
}
