"""
EPIPHANY INTEGRATION VERIFIER - END-TO-END SYSTEM TEST
"""
# pylint: disable=no-value-for-parameter
import os
import sys
from dataclasses import dataclass
from typing import Any
from web3 import Web3
from eth_account import Account
import solcx
from appraisal_engine import AppraisalEngine, AppraisalMetrics, AppraisalParams

# ==============================================================================
# EPIPHANY INTEGRATION VERIFIER - END-TO-END SYSTEM TEST
# ==============================================================================

@dataclass
class AuthConfig:
    """Container for authorization configuration."""
    deployer: str
    appraiser_addr: str
    buyer_acc: str

@dataclass
class ProtocolStack:
    """Container for deployed contracts."""
    ledger: Any
    registry: Any
    dar: Any

def compile_contract(file_path, contract_name, node_modules_path):
    """Compiles a Solidity contract with OpenZeppelin remappings."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    settings = {
        "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}},
        "remappings": [
            f"@openzeppelin/={node_modules_path}/@openzeppelin/"
        ]
    }

    compiled = solcx.compile_standard({
        "language": "Solidity",
        "sources": {os.path.basename(file_path): {"content": source}},
        "settings": settings
    }, allow_paths=node_modules_path)

    if "errors" in compiled:
        for error in compiled["errors"]:
            if error["severity"] == "error":
                print(f"❌ Compilation Error: {error['message']}")
        if any(e["severity"] == "error" for e in compiled["errors"]):
            sys.exit(1)

    return compiled["contracts"][os.path.basename(file_path)][contract_name]

def deploy_contract(w3, data, args, deployer):
    """Deploys a contract and returns the contract instance."""
    contract = w3.eth.contract(abi=data["abi"], bytecode=data["evm"]["bytecode"]["object"])
    tx_hash = contract.constructor(*args).transact({"from": deployer})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return w3.eth.contract(address=receipt.contractAddress, abi=data["abi"])

def setup_protocol_stack(w3, deployer, node_modules_path):
    """Compiles and deploys the full protocol contract stack."""
    print("⏳ Compiling contracts...")
    ledger_data = compile_contract("src/contracts/ProvenanceLedger.sol",
                                 "ProvenanceLedger", node_modules_path)
    registry_data = compile_contract("src/contracts/ProvenanceRegistry.sol",
                                   "ProvenanceRegistry", node_modules_path)
    dar_data = compile_contract("src/contracts/DataAssetRegistry.sol",
                              "DataAssetRegistry", node_modules_path)

    print("⏳ Deploying Protocol Stack...")
    ledger = deploy_contract(w3, ledger_data, [deployer], deployer)
    registry = deploy_contract(w3, registry_data, [ledger.address], deployer)
    dar = deploy_contract(w3, dar_data, [ledger.address, registry.address], deployer)

    return ProtocolStack(ledger, registry, dar)

def configure_authorizations(w3, stack, config: AuthConfig):
    """Configures roles, appraiser authorizations, and initial funding."""
    print("⏳ Configuring roles and authorizations...")
    minter_role_bytes = w3.keccak(text="MINTER_ROLE")
    stack.registry.functions.grantRole(minter_role_bytes, stack.dar.address).transact(
        {"from": config.deployer})
    stack.dar.functions.setAppraiser(config.appraiser_addr, True).transact(
        {"from": config.deployer})

    report_id = w3.keccak(text="initial_funding")
    stack.ledger.functions.anchorIntelligenceReport(report_id, 1000000 * 10**18).transact(
        {"from": config.buyer_acc})
    stack.ledger.functions.verifyIntelligenceReport(report_id).transact({"from": config.deployer})
    stack.ledger.functions.claimCredits().transact({"from": config.buyer_acc})

    buyer_balance = stack.ledger.functions.balanceOf(config.buyer_acc).call()
    print(f"✓ Buyer funded with {buyer_balance / 10**18} EIT tokens.")

def execute_purchase(ledger, dar, appraisal_result, buyer_acc):
    """Executes the on-chain purchase of a data asset."""
    price_eit_wei = appraisal_result["appraisal"]["price"]
    ledger.functions.approve(dar.address, price_eit_wei).transact({"from": buyer_acc})

    app_res = appraisal_result["appraisal"]
    appraisal_payload = (
        app_res["dataHash"],
        app_res["price"],
        app_res["ipfsCID"],
        app_res["nonce"],
        app_res["expiry"],
        app_res["creator"]
    )
    sig_hex = appraisal_result["signature"]
    signature = bytes.fromhex(sig_hex[2:]) if sig_hex.startswith("0x") else bytes.fromhex(sig_hex)

    tx_hash = dar.functions.purchaseAsset(appraisal_payload, signature).transact(
        {"from": buyer_acc})
    return tx_hash

def perform_appraisal(engine, creator_acc):
    """Performs the appraisal and returns the result."""
    data_hash = Web3.keccak(text="Top Secret Forensic Evidence")
    metrics = AppraisalMetrics(base_cost=500.0, information_density=1.5,
                              scarcity_metric=2.0, demand_vector=1.2)
    valuation_usd = engine.calculate_valuation(metrics)
    price = engine.usd_to_eit_wei(valuation_usd)
    params = AppraisalParams(data_hash=data_hash, price_eit_wei=price,
                            ipfs_cid="QmTest123456789", creator_address=creator_acc, nonce=1)
    appraisal_result = engine.generate_appraisal_signature(params)
    return appraisal_result, valuation_usd, data_hash

def check_outcomes(stack, buyer_acc, data_hash, app_res):
    """Verifies the final state of the blockchain after purchase."""
    print("⏳ Verifying outcomes...")
    has_access = stack.dar.functions.accessGrants(buyer_acc, data_hash).call()
    nft_bal = stack.registry.functions.balanceOf(buyer_acc).call()
    creator_bal = stack.ledger.functions.balanceOf(app_res["appraisal"]["creator"]).call()

    print(f"✓ Access Grant: {has_access}, NFT Balance: {nft_bal}")
    print(f"✓ Creator EIT Balance: {creator_bal / 10**18} tokens")

    if has_access and nft_bal == 1 and creator_bal == app_res["appraisal"]["price"]:
        print("\n✨ INTEGRATION VERIFIED SUCCESSFULLY ✨\n")
    else:
        print("\n❌ VERIFICATION FAILED ❌\n")
        sys.exit(1)

def setup_test_env():
    """Sets up the test environment: w3, accounts, and solc."""
    w3 = Web3(Web3.EthereumTesterProvider())
    # pylint: disable=unbalanced-tuple-unpacking
    deployer, creator_acc, buyer_acc = w3.eth.accounts[0:3]
    app_acc = Account.create()

    if "0.8.26" not in [str(v) for v in solcx.get_installed_solc_versions()]:
        solcx.install_solc("0.8.26")
    solcx.set_solc_version("0.8.26")
    return w3, deployer, creator_acc, buyer_acc, app_acc

def verify_integration():
    """Main integration verification logic."""
    print("🧪 Starting End-to-End Integration Verification...")
    w3, deployer, creator_acc, buyer_acc, app_acc = setup_test_env()

    stack = setup_protocol_stack(w3, deployer, os.path.abspath("node_modules"))

    auth_config = AuthConfig(deployer, app_acc.address, buyer_acc)
    configure_authorizations(w3, stack, auth_config)

    print("⏳ Running Appraisal Engine...")
    engine = AppraisalEngine(app_acc.key, w3.eth.chain_id, stack.dar.address)
    app_res, val, d_hash = perform_appraisal(engine, creator_acc)
    print(f"✓ Appraisal signed. Price: {val} USD")

    tx_h = execute_purchase(stack.ledger, stack.dar, app_res, buyer_acc)
    print(f"✅ Purchase Successful! Hash: {tx_h.hex()}")

    check_outcomes(stack, buyer_acc, d_hash, app_res)

if __name__ == "__main__":
    verify_integration()
