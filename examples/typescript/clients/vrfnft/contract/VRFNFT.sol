// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// import {console} from "forge-std/Test.sol"; // Keep commented out

import {VRFV2PlusClient} from "@chainlink/contracts/v0.8/vrf/dev/libraries/VRFV2PlusClient.sol"; // Add back
import {VRFV2PlusWrapperConsumerBase} from "@chainlink/contracts/v0.8/vrf/dev/VRFV2PlusWrapperConsumerBase.sol";
// Use ERC721URIStorage for custom token URIs
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol"; // Import base ERC721
import {ERC721URIStorage} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
// Import Counters and Base64
import {Counters} from "@openzeppelin/contracts/utils/Counters.sol";
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol"; // Needed for uint->string conversion

/**
 * @title VRFNFT
 * @notice A simple NFT contract that uses Chainlink VRF v2.5 to randomly select a character.
 * @dev Inherits from ERC721URIStorage, VRFV2PlusWrapperConsumerBase, and Ownable.
 */
// Inherit from ERC721URIStorage instead of ERC721
contract VRFNFT is ERC721, ERC721URIStorage, VRFV2PlusWrapperConsumerBase, Ownable {
    using Counters for Counters.Counter;
    using Strings for uint256; // Use Strings library

    // VRF Configuration
    bytes32 private immutable _keyHash; // Make immutable if set only once
    uint32 private _callbackGasLimit; // Keep mutable
    uint16 private _requestConfirmations; // Keep mutable
    uint32 private constant _NUM_WORDS = 1;
    uint256 private constant _MINT_PRICE = 0.0001 ether;

    // NFT Minting State
    Counters.Counter private _tokenIdCounter; // Counter for sequential token IDs

    // Character Data (from Runners.sol example)
    string[] private s_characterImages = [
        "https://ipfs.io/ipfs/QmTgqnhFBMkfT9s8PHKcdXBn1f5bG3Q5hmBaR4U6hoTvb1?filename=Chainlink_Elf.png",
        "https://ipfs.io/ipfs/QmZGQA92ri1jfzSu61JRaNQXYg1bLuM7p8YT83DzFA2KLH?filename=Chainlink_Knight.png",
        "https://ipfs.io/ipfs/QmW1toapYs7M29rzLXTENn3pbvwe8ioikX1PwzACzjfdHP?filename=Chainlink_Orc.png",
        "https://ipfs.io/ipfs/QmPMwQtFpEdKrUjpQJfoTeZS1aVSeuJT6Mof7uV29AcUpF?filename=Chainlink_Witch.png"
    ];
    string[] private s_characterNames = [
        "Chainlink Elf",
        "Chainlink Knight",
        "Chainlink Orc",
        "Chainlink Witch"
    ];

    mapping(uint256 => uint256) private s_tokenIdToCharacterIndex; // tokenId -> character index (0-3)

    // VRF Request State
    struct RequestStatus {
        bool fulfilled;
        bool exists;
        uint256[] randomWords;
    }
    mapping(uint256 => RequestStatus) public s_requests;
    mapping(uint256 => address) public s_requestIdToRecipient;

    // Events
    event RequestSent(uint256 requestId, address requester, uint256 paid);
    event RequestFulfilled(uint256 requestId, uint256[] randomWords);
    event NFTMinted(uint256 requestId, address owner, uint256 tokenId, uint256 characterIndex);


    /**
     * @param vrfWrapper Address of the Chainlink VRF Wrapper
     * @param keyHash The gas lane key hash
     * @param callbackGasLimit Maximum gas for the callback
     * @param requestConfirmations Minimum block confirmations
     */
    constructor(
        address vrfWrapper,
        bytes32 keyHash,
        uint32 callbackGasLimit,
        uint16 requestConfirmations
    )
        ERC721("VRFNFT", "VRF") // Call ERC721 constructor with name/symbol
        // ERC721URIStorage() // No constructor args for ERC721URIStorage
        VRFV2PlusWrapperConsumerBase(vrfWrapper)
        Ownable() // Correct: Ownable constructor takes no args in this version
    {
        _keyHash = keyHash;
        _callbackGasLimit = callbackGasLimit;
        _requestConfirmations = requestConfirmations;
        // Token counter starts at 0 implicitly
    }

    /**
     * @notice Request a new NFT backed by a random number from Chainlink VRF (Direct Native Funding).
     * @dev Pays VRF fees in native token (ETH) via the VRFV2PlusWrapperConsumerBase contract.
     * @dev Requires msg.value >= (calculated VRF fee + _MINT_PRICE).
     * @dev The _MINT_PRICE remains in this contract's balance.
     * @param _recipient The address that will receive the NFT upon fulfillment.
     * @return requestId The ID of the VRF request.
     */
    function requestNFT(address _recipient) external payable returns (uint256 requestId) {
        require(_recipient != address(0), "Recipient cannot be zero address");
        uint256 vrfFee = i_vrfV2PlusWrapper.calculateRequestPriceNative(_callbackGasLimit, _NUM_WORDS);
        require(msg.value >= vrfFee + _MINT_PRICE, "Insufficient payment (VRF fee + mint price)");

        bytes memory encodedArgs = abi.encode(VRFV2PlusClient.ExtraArgsV1({nativePayment: true}));
        bytes memory extraArgs = bytes.concat(VRFV2PlusClient.EXTRA_ARGS_V1_TAG, encodedArgs);

        (requestId, /*uint256 requestPrice*/) = requestRandomnessPayInNative(
            _callbackGasLimit,
            _requestConfirmations,
            _NUM_WORDS,
            extraArgs
        );

        s_requests[requestId] = RequestStatus({fulfilled: false, exists: true, randomWords: new uint256[](0)});
        s_requestIdToRecipient[requestId] = _recipient;

        emit RequestSent(requestId, msg.sender, vrfFee);
        return requestId;
    }

    /**
     * @notice Callback function used by the VRF Coordinator Wrapper to return random words.
     * @dev Selects a character based on the random word and mints an NFT with a sequential ID.
     * @dev This function MUST be callable by the VRF Wrapper (via Base's rawFulfillRandomWords).
     * @param requestId The unique identifier of the request.
     * @param randomWords The random words delivered by the VRF.
     */
    function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal override {
        require(s_requests[requestId].exists, "Request not found");
        require(!s_requests[requestId].fulfilled, "Request already fulfilled");
        require(randomWords.length > 0, "No random words received");

        s_requests[requestId].fulfilled = true;
        s_requests[requestId].randomWords = randomWords;

        address owner = s_requestIdToRecipient[requestId];
        require(owner != address(0), "Recipient address cannot be zero");

        // Use random word to select character index
        uint256 characterIndex = randomWords[0] % s_characterNames.length;

        // Get next tokenId and increment counter
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();

        // Store the chosen character for this tokenId
        s_tokenIdToCharacterIndex[tokenId] = characterIndex;

        // Mint the NFT with the sequential tokenId
        _safeMint(owner, tokenId);

        // Construct and set the token URI
        string memory characterName = s_characterNames[characterIndex];
        string memory characterImageURI = s_characterImages[characterIndex];

        string memory json = Base64.encode(
            bytes(
                string(
                    abi.encodePacked(
                        '{',
                        '"name": "', characterName, ' #', tokenId.toString(), '",',
                        '"description": "A randomly generated VRFNFT character.",',
                        '"image": "', characterImageURI, '",',
                        '"attributes": [',
                            '{',
                                '"trait_type": "Character", ',
                                '"value": "', characterName, '"',
                            '}',
                        ']',
                        '}'
                    )
                )
            )
        );
        string memory finalTokenURI = string(abi.encodePacked("data:application/json;base64,", json));
        _setTokenURI(tokenId, finalTokenURI);

        // Clean up recipient mapping
        delete s_requestIdToRecipient[requestId];

        emit RequestFulfilled(requestId, randomWords);
        emit NFTMinted(requestId, owner, tokenId, characterIndex);
    }

    // --- Overrides for Inheritance Conflicts ---

    /**
     * @dev See {ERC721-_burn}.
     */
     function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
         super._burn(tokenId);
         // Optional: Clear the character index mapping if desired, though not strictly necessary
         // delete s_tokenIdToCharacterIndex[tokenId];
     }

    /**
     * @dev See {ERC721URIStorage-tokenURI}.
     * Required due to inheritance from both ERC721 and ERC721URIStorage.
     */
    function tokenURI(uint256 tokenId) public view virtual override(ERC721, ERC721URIStorage) returns (string memory) {
        // Use the implementation from ERC721URIStorage
        return super.tokenURI(tokenId);
    }

    /**
     * @dev See {ERC165-supportsInterface}.
     * Required due to inheritance from both ERC721 and ERC721URIStorage.
     */
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721, ERC721URIStorage) returns (bool) {
        // Let Solidity handle combining the results from base classes
        return super.supportsInterface(interfaceId);
    }

    // --- Getter Functions ---

    function getRequestStatus(
        uint256 requestId
    ) external view returns (bool fulfilled, uint256[] memory randomWords) {
        require(s_requests[requestId].exists, "Request not found");
        RequestStatus memory request = s_requests[requestId];
        return (request.fulfilled, request.randomWords);
    }

    // getVRFWrapper() is inherited from Base

    function getRequestConfig()
        external
        view
        returns (bytes32 keyHash, uint32 callbackGasLimit, uint16 requestConfirmations, uint32 numWords)
    {
        return (
            _keyHash,
            _callbackGasLimit,
            _requestConfirmations,
            _NUM_WORDS
        );
    }

     function getMintPrice() external pure returns (uint256) {
         return _MINT_PRICE;
     }

    // --- Owner Functions ---

    function setCallbackGasLimit(uint32 callbackGasLimit) external onlyOwner {
        _callbackGasLimit = callbackGasLimit;
    }

    function setRequestConfirmations(uint16 requestConfirmations) external onlyOwner {
        _requestConfirmations = requestConfirmations;
    }

    function withdrawNative(address payable to) external onlyOwner {
        uint256 amount = address(this).balance;
        require(amount > 0, "No native balance to withdraw");
        (bool success,) = to.call{value: amount}("");
        require(success, "Native token transfer failed");
    }
} 