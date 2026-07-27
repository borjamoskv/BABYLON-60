// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

/// @title BABYLON60-Persist Ouroboros Yul Executor
/// @notice P0 Direct-Silicon execution path for Genesis Block Snipe
contract OuroborosExecutor {
    address private immutable SOVEREIGN;

    constructor() {
        SOVEREIGN = msg.sender;
    }

    /// @notice Executing bare-metal call to UniswapV2Router
    function genesisSnipe(
        address router,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable {
        // Validación Soberana C5-REAL
        require(msg.sender == SOVEREIGN, "NO_AUTH");

        // Limitamos a path de tamaño 2 por velocidad de O(1)
        require(path.length == 2, "PATH_2_ONLY");

        // Inline Yul for swapExactETHForTokens
        assembly {
            // El objetivo: optimizar los desplazamientos de memoria y evitar overhead de ABI encoder
            // Selector: swapExactETHForTokens(uint256,address[],address,uint256) -> 0x7ff36ab5

            let ptr := mload(0x40)

            // Selector
            mstore(ptr, 0x7ff36ab500000000000000000000000000000000000000000000000000000000)

            // Param 1: amountOutMin
            mstore(add(ptr, 0x04), amountOutMin)

            // Param 2: path offset (128 bytes of offset, due to 4 params)
            mstore(add(ptr, 0x24), 0x80)

            // Param 3: to address
            mstore(add(ptr, 0x44), to)

            // Param 4: deadline
            mstore(add(ptr, 0x64), deadline)

            // Array length = 2
            mstore(add(ptr, 0x84), 0x02)

            // Path elements
            let path0 := calldataload(path.offset)
            let path1 := calldataload(add(path.offset, 0x20))

            mstore(add(ptr, 0xa4), path0)
            mstore(add(ptr, 0xc4), path1)

            // Ejecución CALL (saltando revert messages por eficiencia P0)
            let success := call(
                gas(),       // Enviar todo el gas restante
                router,      // UniswapV2Router
                callvalue(), // Enviar ETH asociado a la transacción
                ptr,         // args memory start
                0xe4,        // args size (4 + 32*4 + 32 + 32*2 = 228 = 0xe4)
                0,           // no return data start
                0            // no return data length
            )

            if iszero(success) {
                revert(0, 0) // Die fast para ahorrar gas si falla
            }
        }
    }

    /// @notice Liquidar tokens por ETH en el bloque de salida (T+5m o 100x)
    function liquidate(
        address router,
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external {
        require(msg.sender == SOVEREIGN, "NO_AUTH");
        require(path.length == 2, "PATH_2_ONLY");

        // Inline Yul for swapExactTokensForETHSupportingFeeOnTransferTokens
        assembly {
            // Selector: swapExactTokensForETHSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)
            // Selector hash: 0x791ac947

            let ptr := mload(0x40)
            mstore(ptr, 0x791ac94700000000000000000000000000000000000000000000000000000000)

            mstore(add(ptr, 0x04), amountIn)
            mstore(add(ptr, 0x24), amountOutMin)
            mstore(add(ptr, 0x44), 0xa0) // Path offset
            mstore(add(ptr, 0x64), to)
            mstore(add(ptr, 0x84), deadline)

            mstore(add(ptr, 0xa4), 0x02) // Path length

            let path0 := calldataload(path.offset)
            let path1 := calldataload(add(path.offset, 0x20))

            mstore(add(ptr, 0xc4), path0)
            mstore(add(ptr, 0xe4), path1)

            // Aprobar router para gastar tokens (esto suele hacerse una vez, pero aquí lo forzamos si es necesario)
            // En un sniper real, se hace un "Infinite Approve" previo al Router para el token adquirente.

            let success := call(gas(), router, 0, ptr, 0x104, 0, 0)
            if iszero(success) {
                revert(0, 0)
            }
        }
    }

    /// @notice Para retirar el lucro obtenido a la wallet maestra
    function extractCapital(address token, uint256 amount) external {
        require(msg.sender == SOVEREIGN, "NO_AUTH");
        if (token == address(0)) {
            (bool success, ) = msg.sender.call{value: address(this).balance}("");
            require(success, "ETH_TRANSFER_FAIL");
        } else {
            // Low-level token transfer
            (bool success, ) = token.call(
                abi.encodeWithSignature("transfer(address,uint256)", msg.sender, amount)
            );
            require(success, "TX_FAIL");
        }
    }

    /// @notice Pre-autorizar al Router para liquidación rápida.
    /// Elimina la necesidad de aprobar el token en el bloque de salida.
    function infiniteApprove(address router, address token) external {
        require(msg.sender == SOVEREIGN, "NO_AUTH");
        (bool success, ) = token.call(
            abi.encodeWithSignature("approve(address,uint256)", router, type(uint256).max)
        );
        require(success, "APPROVE_FAIL");
    }

    receive() external payable {}
}
