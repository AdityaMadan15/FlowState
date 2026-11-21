// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract FlowStatePayout is Ownable, ReentrancyGuard {
    uint256 public constant PAYOUT_AMOUNT = 0.0005 ether; // Simulates ₹500.

    event PayoutTriggered(
        address indexed worker,
        uint256 amount,
        uint256 timestamp
    );

    constructor() Ownable(msg.sender) {}

    function fundPool() external payable {}

    function triggerPayout(address payable _worker)
        external
        onlyOwner
        nonReentrant
    {
        require(address(this).balance >= PAYOUT_AMOUNT, "Pool empty");
        (bool success, ) = _worker.call{value: PAYOUT_AMOUNT}("");
        require(success, "Payout transfer failed");
        emit PayoutTriggered(_worker, PAYOUT_AMOUNT, block.timestamp);
    }

    function poolBalance() external view returns (uint256) {
        return address(this).balance;
    }

    // Production deployments should add a daily payout limit.
}
