pragma solidity ^0.8.19;

/// @title Anvil Apoptosis Anchor (Trilingual Regime)
/// @dev Yunque de consenso determinista para asentar CORTEX-TAINT y colapsos C5-REAL.
///      Modelo Single-Writer (ver STATUS.md): un unico escritor autorizado muta el
///      head canonico. commitState y logApoptosis eran `external` sin control de
///      acceso — cualquier EOA reescribia currentHead. Ahora ambas son onlyWriter.
contract ApoptosisAnchor {
    string public currentHead;
    uint256 public latentSteps;

    /// @dev Escritor autorizado (Single-Writer). Fijado en el constructor,
    ///      transferible solo por si mismo.
    address public writer;

    error Unauthorized(address caller);
    error ZeroAddress();

    event MembraneStateCommitted(string prevHead, string newHead, uint256 latentSteps);
    event ApoptosisLogged(string taint, string reason);
    event WriterTransferred(address indexed previousWriter, address indexed newWriter);

    modifier onlyWriter() {
        if (msg.sender != writer) revert Unauthorized(msg.sender);
        _;
    }

    constructor(string memory genesisHash) {
        currentHead = genesisHash;
        latentSteps = 0;
        writer = msg.sender;
        emit WriterTransferred(address(0), msg.sender);
    }

    /// @notice Transfiere el rol de escritor unico. Rechaza address(0) para no
    ///         dejar el ancla sin escritor de forma irreversible.
    function transferWriter(address newWriter) external onlyWriter {
        if (newWriter == address(0)) revert ZeroAddress();
        emit WriterTransferred(writer, newWriter);
        writer = newWriter;
    }

    /// @notice Avanza el head si inputHash casa con el head actual.
    /// @dev El require de fork es defensa en profundidad SOBRE el control de
    ///      acceso: antes era el unico control, y como currentHead es public el
    ///      atacante lo leia y lo satisfacia. onlyWriter cierra ese vector.
    ///      latentSteps += steps no puede desbordar de forma silenciosa: la
    ///      aritmetica de solidity >=0.8 revierte en overflow (checked math).
    function commitState(string calldata inputHash, string calldata outputHash, uint256 steps) external onlyWriter {
        require(keccak256(abi.encodePacked(currentHead)) == keccak256(abi.encodePacked(inputHash)), "BFT_FORK_DETECTED: Input hash does not match current head");

        string memory prev = currentHead;
        currentHead = outputHash;
        latentSteps += steps;

        emit MembraneStateCommitted(prev, currentHead, latentSteps);
    }

    /// @notice Colapso de apoptosis: trunca el head. Anula la disciplina de
    ///         commitState, por lo que DEBE estar restringida al escritor unico.
    function logApoptosis(string calldata taintLog, string calldata reason) external onlyWriter {
        currentHead = taintLog;
        latentSteps = 0; // Truncation
        emit ApoptosisLogged(taintLog, reason);
    }
}
