// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

/**
 * @title ParametricClimateRelief
 * @notice Protocolo de Desembolso Paramétrico y Anclaje de Integridad de Datos EDAN.
 * @dev Diseñado para el certamen IEEE ClimateChain Global Hackathon 2026 (COP31).
 * 
 * Resuelve la parálisis burocrática y el fraude en la ayuda humanitaria:
 * 1. Opera como receptor de atestados criptográficos firmados por el Oráculo AMARU-FEN.
 * 2. Verifica on-chain que los datos de aforo hidrológico o anomalía de temperatura del mar (TSM)
 *    hayan superado los umbrales críticos definidos en la doctrina CAF/PUCP 2026.
 * 3. Ejecuta el desembolso paramétrico instantáneo de fondos de contingencia a comités y municipios.
 * 4. Ancla de manera inmutable el hash criptográfico de la Ficha EDAN (Evaluación de Daños).
 */
contract ParametricClimateRelief {
    // --- ESTADOS Y CONSTANTES ---
    address public immutable admin;
    address public amaruOracleSigner;

    // Umbrales Paramétricos Oficiales (ej. Cuenca del Río Piura / Catacaos)
    uint256 public constant UMBRAL_CAUDAL_CRITICO_M3S = 1900; // 1,900 m3/s = Alerta Roja Inundación
    
    // Mapeo de Ubigeo a Dirección del Municipio / Comité de Regantes acreditado
    mapping(string => address payable) public beneficiariosDistritales;

    // Registro inmutable de eventos procesados para prevenir ataques de repetición (Replay Attacks)
    mapping(bytes32 => bool) public executedAttestations;
    mapping(bytes32 => bool) public anchoredEdanReports;

    // --- EVENTOS AUDITABLES ON-CHAIN ---
    event OracleSignerUpdated(address indexed previousSigner, address indexed newSigner);
    event BeneficiaryRegistered(string indexed ubigeo, address indexed beneficiary);
    event ClimateDisasterDeclared(
        string indexed ubigeo,
        uint256 caudalM3s,
        bytes32 indexed edanHash,
        uint256 timestamp
    );
    event ParametricFundDisbursed(
        string indexed ubigeo,
        address indexed recipient,
        uint256 amountWei,
        uint256 timestamp
    );
    event EdanReportAnchored(
        string indexed ubigeo,
        bytes32 indexed edanHash,
        uint256 timestamp
    );

    // --- MODIFICADORES ---
    modifier onlyAdmin() {
        require(msg.sender == admin, "Solo el Administrador del Sistema puede ejecutar esta accion");
        _;
    }

    constructor(address _initialOracleSigner) {
        require(_initialOracleSigner != address(0), "Direccion de oraculo invalida");
        admin = msg.sender;
        amaruOracleSigner = _initialOracleSigner;
        emit OracleSignerUpdated(address(0), _initialOracleSigner);
    }

    /**
     * @notice Permite fondear la bóveda de emergencia (MEF Programa Presupuestal PP 0068 / Fondos Multilaterales).
     */
    receive() external payable {}

    /**
     * @notice Registra o actualiza la billetera del municipio o junta de regantes acreditada para un Ubigeo.
     */
    function setBeneficiarioDistrital(string calldata _ubigeo, address payable _beneficiario) external onlyAdmin {
        require(_beneficiario != address(0), "Direccion de beneficiario invalida");
        beneficiariosDistritales[_ubigeo] = _beneficiario;
        emit BeneficiaryRegistered(_ubigeo, _beneficiario);
    }

    /**
     * @notice Actualiza la clave pública del Oráculo de IA AMARU-FEN.
     */
    function setOracleSigner(address _newSigner) external onlyAdmin {
        require(_newSigner != address(0), "Direccion invalida");
        emit OracleSignerUpdated(amaruOracleSigner, _newSigner);
        amaruOracleSigner = _newSigner;
    }

    /**
     * @notice Procesa el atestado del Oráculo y ejecuta la liquidación paramétrica si se cumple el umbral.
     * @param _ubigeo Código de ubicación geográfica del distrito afectado (ej. "200105" para Catacaos).
     * @param _caudalM3s Caudal certificado por los sensores de aforo de AMARU-FEN.
     * @param _edanHash Hash SHA-256 de la Ficha EDAN generada por el agente de despacho.
     * @param _nonce Número único para prevenir repetición.
     * @param _signature Firma criptográfica generada por la clave privada del Oráculo AMARU.
     */
    function executeParametricTrigger(
        string calldata _ubigeo,
        uint256 _caudalM3s,
        bytes32 _edanHash,
        uint256 _nonce,
        bytes calldata _signature
    ) external {
        bytes32 messageHash = keccak256(
            abi.encodePacked(_ubigeo, _caudalM3s, _edanHash, _nonce, block.chainid)
        );
        bytes32 ethSignedMessageHash = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", messageHash)
        );

        require(!executedAttestations[messageHash], "Este atestado ya fue liquidado previamente (Anti-Replay)");
        require(recoverSigner(ethSignedMessageHash, _signature) == amaruOracleSigner, "Firma de Oraculo AMARU invalida");

        executedAttestations[messageHash] = true;

        // Anclaje inmutable del informe de daños EDAN para auditoria de Contraloria y COP31
        if (!anchoredEdanReports[_edanHash] && _edanHash != bytes32(0)) {
            anchoredEdanReports[_edanHash] = true;
            emit EdanReportAnchored(_ubigeo, _edanHash, block.timestamp);
        }

        emit ClimateDisasterDeclared(_ubigeo, _caudalM3s, _edanHash, block.timestamp);

        // Verificacion del trigger parametrico
        if (_caudalM3s >= UMBRAL_CAUDAL_CRITICO_M3S) {
            address payable recipient = beneficiariosDistritales[_ubigeo];
            require(recipient != address(0), "No hay billetera registrada para este Ubigeo distrital");

            uint256 contractBalance = address(this).balance;
            uint256 disbursementAmount = contractBalance > 0 ? contractBalance / 2 : 0; // Regla: Desembolso del 50% de la reserva inmediata

            if (disbursementAmount > 0) {
                (bool success, ) = recipient.call{value: disbursementAmount}("");
                require(success, "Fallo la transferencia del fondo humanitario");
                emit ParametricFundDisbursed(_ubigeo, recipient, disbursementAmount, block.timestamp);
            }
        }
    }

    /**
     * @dev Recupera la direccion del firmante a partir del hash y la firma.
     */
    function recoverSigner(bytes32 _ethSignedMessageHash, bytes memory _sig) internal pure returns (address) {
        require(_sig.length == 65, "Longitud de firma invalida");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(_sig, 32))
            s := mload(add(_sig, 64))
            v := byte(0, mload(add(_sig, 96)))
        }

        return ecrecover(_ethSignedMessageHash, v, r, s);
    }
}
