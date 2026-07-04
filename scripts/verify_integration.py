"""
EPIPHANY INTEGRATION VERIFIER - END-TO-END SYSTEM TEST
"""
import os
import sys
from web3 import Web3
from eth_account import Account
import solcx
from appraisal_engine import AppraisalEngine, AppraisalMetrics, AppraisalParams

# ==============================================================================
# EPIPHANY INTEGRATION VERIFIER - END-TO-END SYSTEM TEST
# ==============================================================================

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

def verify_integration():
    """Main integration verification logic."""
    print("🧪 Starting End-to-End Integration Verification...")

    # 1. Setup Provider & Accounts
    w3 = Web3(Web3.EthereumTesterProvider())
    accounts = w3.eth.accounts
    deployer = accounts[0]
    appraiser_acc = Account.create()
    creator_acc = accounts[1]
    buyer_acc = accounts[2]

    print(f"✓ Accounts initialized. Deployer: {deployer}")
    print(f"✓ Appraiser: {appraiser_acc.address}")

    # 2. Compile and Deploy Contracts
    print("⏳ Checking Solc 0.8.26...")
    if "0.8.26" not in [str(v) for v in solcx.get_installed_solc_versions()]:
        solcx.install_solc("0.8.26")
    solcx.set_solc_version("0.8.26")

    node_modules_path = os.path.abspath("node_modules")

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

    print(f"✅ Ledger (EIT): {ledger.address}")
    print(f"✅ Registry: {registry.address}")
    print(f"✅ DataAssetRegistry: {dar.address}")

    # 3. Configure Roles
    print("⏳ Configuring roles and authorizations...")
    minter_role_bytes = w3.keccak(text="MINTER_ROLE")
    registry.functions.grantRole(minter_role_bytes, dar.address).transact({"from": deployer})
    dar.functions.setAppraiser(appraiser_acc.address, True).transact({"from": deployer})

    report_id = w3.keccak(text="initial_funding")
    ledger.functions.anchorIntelligenceReport(report_id, 1000000 * 10**18).transact(
        {"from": buyer_acc})
    ledger.functions.verifyIntelligenceReport(report_id).transact({"from": deployer})
    ledger.functions.claimCredits().transact({"from": buyer_acc})

    buyer_balance = ledger.functions.balanceOf(buyer_acc).call()
    print(f"✓ Buyer funded with {buyer_balance / 10**18} EIT tokens.")

    # 4. Engine Appraisal
    print("⏳ Running Appraisal Engine...")
    engine = AppraisalEngine(appraiser_acc.key, w3.eth.chain_id, dar.address)

    data_hash = w3.keccak(text="Top Secret Forensic Evidence")
    ipfs_cid = "QmTest123456789"

    metrics = AppraisalMetrics(base_cost=500.0, information_density=1.5,
                              scarcity_metric=2.0, demand_vector=1.2)
    valuation_usd = engine.calculate_valuation(metrics)
    price_eit_wei = engine.usd_to_eit_wei(valuation_usd)

    params = AppraisalParams(
        data_hash=data_hash, # Use bytes directly
        price_eit_wei=price_eit_wei,
        ipfs_cid=ipfs_cid,
        creator_address=creator_acc,
        nonce=1
    )
    appraisal_result = engine.generate_appraisal_signature(params)
    print(f"✓ Appraisal signed. Price: {valuation_usd} USD ({price_eit_wei} units)")

    # 5. On-Chain Purchase
    print("⏳ Executing on-chain purchase...")
    ledger.functions.approve(dar.address, price_eit_wei).transact({"from": buyer_acc})

    appraisal_payload = (
        appraisal_result["appraisal"]["dataHash"],
        appraisal_result["appraisal"]["price"],
        appraisal_result["appraisal"]["ipfsCID"],
        appraisal_result["appraisal"]["nonce"],
        appraisal_result["appraisal"]["expiry"],
        appraisal_result["appraisal"]["creator"]
    )
    sig_hex = appraisal_result["signature"]
    signature = bytes.fromhex(sig_hex[2:]) if sig_hex.startswith("0x") else bytes.fromhex(sig_hex)

    tx_hash = dar.functions.purchaseAsset(appraisal_payload, signature).transact({"from": buyer_acc})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Purchase Successful! Hash: {receipt.transactionHash.hex()}")

    # 6. Verification
    print("⏳ Verifying outcomes...")
    has_access = dar.functions.accessGrants(buyer_acc, data_hash).call()
    nft_balance = registry.functions.balanceOf(buyer_acc).call()
    creator_balance = ledger.functions.balanceOf(creator_acc).call()

    print(f"✓ Access Grant: {has_access}")
    print(f"✓ NFT Balance: {nft_balance}")
    print(f"✓ Creator EIT: {creator_balance / 10**18} tokens")

    if has_access and nft_balance == 1 and creator_balance == price_eit_wei:
        print("\n✨ INTEGRATION VERIFIED SUCCESSFULLY ✨\n")
    else:
        print("\n❌ VERIFICATION FAILED ❌\n")
        sys.exit(1)

if __name__ == "__main__":
    verify_integration()
