// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {OuroborosExecutor} from "../src/OuroborosExecutor.sol";

// Simulador avanzado de un Token Trampa (Honeypot) - Modifica balances silenciosamente o bloquea ventas.
contract MaliciousHoneypotToken {
    mapping(address => uint256) public balanceOf;
    address public owner;

    constructor() { owner = msg.sender; }

    function mint(address to, uint256 amount) external { balanceOf[to] += amount; }

    // El Honeypot: Se puede comprar, pero no se puede vender (excepto el Owner).
    function transfer(address to, uint256 amount) external returns (bool) {
        if (msg.sender != owner && to != owner) {
            revert("HONEYPOT: YOU CANNOT SELL"); // Trampa Mortal
        }
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

contract HoneypotFuzzTest is Test {
    OuroborosExecutor public executor;
    MaliciousHoneypotToken public trapToken;

    address constant UNISWAP_V2_ROUTER_MOCK = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D; // Dummy

    function setUp() public {
        executor = new OuroborosExecutor();
        trapToken = new MaliciousHoneypotToken();
    }

    /// @notice Inyectamos entropía estructural: Fuzz testing del simulador contra el Router
    /// En C5-REAL, el Rust Daemon correría eth_call. Aquí forzamos Foundry a replicar el Revert state.
    function testFuzz_HoneypotSimulation(uint256 buyAmount) public {
        // Limitamos bounds plausibles
        vm.assume(buyAmount > 0.01 ether && buyAmount < 100 ether);

        // Si el Daemon mandara la señal de compra pero el token es trampa, el PnL_Max detona Sell.
        // Simularemos el 'Attempt to Sell'.

        vm.startPrank(address(executor));
        trapToken.mint(address(executor), buyAmount); // Simulación post-buy

        // Esperamos que falle letalmente al intentar limpiar inventario
        vm.expectRevert("HONEYPOT: YOU CANNOT SELL");
        trapToken.transfer(UNISWAP_V2_ROUTER_MOCK, buyAmount);
        vm.stopPrank();
    }
}
