// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

contract TargetToCorrupt {
    uint256 public lockedValue;
    bool public hasExploded;

    constructor() {
        lockedValue = 1000;
        hasExploded = false;
    }

    // Vulnerabilidad inyectada (Underflow lógico por falta de guards bajo Chaos Fuzzing)
    function complexOperation(uint256 x, uint256 y, uint256 z) public {
        unchecked {
            if (x * y + z == 89283471) {
                if (x < 1000 && y > 50000) {
                    hasExploded = true; // El Fuzzer debería hallar este estado imposible a ciegas
                }
            }
        }
    }
}
