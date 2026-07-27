// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.12;

/**
 * @title StrategyManager (Simplified Mock for CORTEX Audit)
 * @notice Focus on withdrawal logic and share arithmetic.
 */
contract StrategyManager {
    
    // Mapping of strategy to user to shares
    mapping(address => mapping(address => uint256)) public stakerStrategyShares;
    mapping(address => uint256) public totalStrategyShares;

    // VULNERABILIDAD IDENTIFICADA: Aritmética de punto fijo sin redondeo explícito
    function getWithdrawalAmount(address strategy, uint256 shares, uint256 totalStake) public view returns (uint256) {
        uint256 totalShares = totalStrategyShares[strategy];
        if (totalShares == 0) return 0;
        
        // [C5-REAL] Vulnerabilidad de redondeo: 
        // Si totalStake ha sido "slashed", esta división trunca hacia abajo (floor), 
        // lo cual beneficia al protocolo. Pero si el fuzzer detectó filtraciones,
        // la implementación real podría tener el multiplicador invertido o falta de validación.
        return (shares * totalStake) / totalShares;
    }

    // TODO: Verificar si se usa Rounding.Down de OpenZeppelin en la implementación real del AVS.
}
