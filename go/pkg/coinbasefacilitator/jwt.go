package coinbasefacilitator

import (
	"fmt"
	"strings"

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
	// Remove https:// if present
	requestHost = strings.TrimPrefix(requestHost, "https://")

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

	bearerToken := fmt.Sprintf("Bearer %s", jwt)

	return bearerToken, nil
}
