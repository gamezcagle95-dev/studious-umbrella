# ==============================================================================
# EPIPHANY WEB3 SETTLEMENT MACHINE - DUAL-CONTRACT DEPLOYMENT ENGINE
# Profile Context: Epiphany Protocol
# ==============================================================================
"""
Deterministic contract deployment engine for the Epiphany Protocol.
Handles sequential deployment of ProvenanceLedger, ProvenanceRegistry, and DataAssetRegistry.
"""
import os
import json
import sys
from dataclasses import dataclass
from typing import List, Any, Dict, Tuple
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

@dataclass
class DeploymentConfig:
    """Container for deployment parameters to reduce function argument count."""
    file_name: str
    contract_name: str
    account: str
    pkey: str
    args: List[Any]

@dataclass
class RoleParams:
    """Container for role delegation parameters."""
    registry_addr: str
    dar_addr: str
    account_address: str
    private_key: str

@dataclass
class MarketConfig:
    """Container for market clearinghouse deployment parameters."""
    account: str
    pkey: str
    ledger: str
    registry: str

load_dotenv()

def get_env_config() -> Tuple[str, str, str]:
    """
    Retrieves and validates environment configuration.

    Returns:
        Tuple[str, str, str]: RPC URL, Private Key, and Account Address.
    """
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    p_key = os.getenv("PRIVATE_KEY", "")
    acc_addr = os.getenv("ACCOUNT_ADDRESS", "")
    return rpc_url, p_key, acc_addr

def delegate_minter_role(w3: Web3, r_params: RoleParams, compiled_sol: Dict[str, Any]) -> None:
    """
    Grants MINTER_ROLE on ProvenanceRegistry to DataAssetRegistry.

    Args:
        w3: Web3 instance.
        r_params: Role parameters dataclass.
        compiled_sol: Dictionary of compiled contracts.
    """
    print("⏳ Delegating MINTER_ROLE to DataAssetRegistry...")
    registry_abi = compiled_sol["contracts"]["ProvenanceRegistry.sol"]["ProvenanceRegistry"]["abi"]
    registry_contract = w3.eth.contract(address=r_params.registry_addr, abi=registry_abi)
    minter_role = w3.keccak(text="MINTER_ROLE")

    nonce = w3.eth.get_transaction_count(r_params.account_address)
    tx_params = {
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": r_params.account_address,
        "nonce": nonce,
    }
    tx = registry_contract.functions.grantRole(
        minter_role, r_params.dar_addr
    ).build_transaction(tx_params)
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=r_params.private_key)
    w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print("✓ MINTER_ROLE granted.")

def deploy_base_protocols(w3: Web3, compiled_sol: Dict[str, Any],
                         account: str, pkey: str) -> Tuple[str, str]:
    """
    Deploys the foundational ProvenanceLedger and ProvenanceRegistry contracts.

    Args:
        w3: Web3 instance.
        compiled_sol: Compiled contract data.
        account: Deployer account address.
        pkey: Private key.

    Returns:
        Tuple[str, str]: Ledger address and Registry address.
    """
    # 1. Deploy ProvenanceLedger
    # ProvenanceLedger serves as the primary transaction and audit logging layer.
    l_cfg = DeploymentConfig("ProvenanceLedger.sol", "ProvenanceLedger",
                             account, pkey, [account])
    ledger_address = deploy_contract(w3, compiled_sol, l_cfg)
    print(f"✅ LEDGER DEPLOYED: {ledger_address}")

    # 2. Deploy ProvenanceRegistry
    # ProvenanceRegistry handles on-chain ownership and NFT-based access control.
    r_cfg = DeploymentConfig("ProvenanceRegistry.sol", "ProvenanceRegistry",
                             account, pkey, [ledger_address])
    registry_address = deploy_contract(w3, compiled_sol, r_cfg)
    print(f"✅ REGISTRY DEPLOYED: {registry_address}")

    return ledger_address, registry_address

def deploy_market_clearinghouse(w3: Web3, compiled_sol: Dict[str, Any],
                               m_cfg: MarketConfig) -> str:
    """
    Deploys the DataAssetRegistry and configures role permissions.

    Args:
        w3: Web3 instance.
        compiled_sol: Compiled contract data.
        m_cfg: Market configuration parameters.

    Returns:
        str: DataAssetRegistry address.
    """
    # 3. Deploy DataAssetRegistry
    # DataAssetRegistry manages the marketplace and appraisal verification logic.
    d_cfg = DeploymentConfig("DataAssetRegistry.sol", "DataAssetRegistry",
                             m_cfg.account, m_cfg.pkey, [m_cfg.ledger, m_cfg.registry])
    dar_address = deploy_contract(w3, compiled_sol, d_cfg)
    print(f"✅ DATA ASSET REGISTRY DEPLOYED: {dar_address}")

    # 4. Role Delegation
    # Grant permission to DAR to mint access NFTs via the Registry contract.
    r_params = RoleParams(m_cfg.registry, dar_address, m_cfg.account, m_cfg.pkey)
    delegate_minter_role(w3, r_params, compiled_sol)

    return dar_address

def run_deployment_loop() -> None:
    """
    Main orchestration loop for deploying protocol contracts.
    This coordinates the entire stack deployment sequence for the Epiphany Protocol.
    """
    print("⛓️  Initializing state machine compiler pipelines...")
    rpc_url, private_key, account_address = get_env_config()

    if not private_key or not account_address:
        print("⚠️  Warning: PRIVATE_KEY or ACCOUNT_ADDRESS not set in environment.")
        print("💡 Simulation Mode: Mocking configuration outputs to public/settlement.json")
        mock_deployment_output(
            "0x4c0883a69102937d6231471b5dbb6204fe302702fd307ce2304598dcf3e346d1",
            "0x71C7656EC7ab88b098defB751B7401B5f6d147a3",
            "0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"
        )
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"❌ Connection Error: Node target offline at {rpc_url}")
        sys.exit(1)

    print(f"✓ Linked to network ledger. Chain ID: {w3.eth.chain_id}")
    install_solc("0.8.26")
    compiled_sol = compile_files()

    ledger_addr, registry_addr = deploy_base_protocols(w3, compiled_sol,
                                                      account_address, private_key)

    m_cfg = MarketConfig(account_address, private_key, ledger_addr, registry_addr)
    dar_addr = deploy_market_clearinghouse(w3, compiled_sol, m_cfg)

    mock_deployment_output(ledger_addr, registry_addr, dar_addr)

def compile_files() -> Dict[str, Any]:
    """
    Compiles Solidity source files using the solc standard JSON input.

    Returns:
        Dict[str, Any]: Standard JSON output from solc.
    """
    files = {
        "ProvenanceLedger.sol": "src/contracts/ProvenanceLedger.sol",
        "ProvenanceRegistry.sol": "src/contracts/ProvenanceRegistry.sol",
        "DataAssetRegistry.sol": "src/contracts/DataAssetRegistry.sol"
    }

    sources = {}
    for name, path in files.items():
        with open(path, "r", encoding="utf-8") as f:
            sources[name] = {"content": f.read()}

    return compile_standard({
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    }, allow_paths=os.path.abspath("node_modules"))

def deploy_contract(w3: Web3, compiled_sol: Dict[str, Any], config: DeploymentConfig) -> str:
    """
    Executes a contract deployment transaction.

    Args:
        w3: Web3 instance.
        compiled_sol: Compiled contract data.
        config: Deployment configuration.

    Returns:
        str: Deployed contract address.
    """
    contract_data = compiled_sol["contracts"][config.file_name][config.contract_name]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    nonce = w3.eth.get_transaction_count(config.account)
    contract_obj = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx_params = {
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": config.account,
        "nonce": nonce,
    }
    tx = contract_obj.constructor(*config.args).build_transaction(tx_params)

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=config.pkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return str(receipt.contractAddress)

def mock_deployment_output(ledger_addr: str, registry_addr: str, dar_addr: str) -> None:
    """
    Synchronizes deployment addresses to public/settlement.json for frontend mapping.

    Args:
        ledger_addr: ProvenanceLedger address.
        registry_addr: ProvenanceRegistry address.
        dar_addr: DataAssetRegistry address.
    """
    settlement_path = "public/settlement.json"
    data = {"contracts": {}}

    if os.path.exists(settlement_path):
        try:
            with open(settlement_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    data["contracts"]["Intelligence_Ledger"] = ledger_addr
    data["contracts"]["Provenance_Registry"] = registry_addr
    data["contracts"]["Data_Asset_Registry"] = dar_addr

    with open(settlement_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✓ Configuration map synchronized in {settlement_path}")

if __name__ == "__main__":
    run_deployment_loop()
