import { createPublicClient, createWalletClient, http, defineChain } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import "dotenv/config";
import fs from "fs";
import path from "path";

const monadTestnet = defineChain({
  id: 10143,
  name: "Monad Testnet",
  nativeCurrency: { name: "MON", symbol: "MON", decimals: 18 },
  rpcUrls: {
    default: { http: ["https://testnet-rpc.monad.xyz"] },
  },
  blockExplorers: {
    default: { name: "MonadExplorer", url: "https://testnet.monadexplorer.com" },
  },
});

async function main() {
  const privateKey = process.env.PRIVATE_KEY;
  if (!privateKey) {
    console.log("PRIVATE_KEY not set in environment. Running in mock mode...");
    mockDeployment();
    return;
  }

  const account = privateKeyToAccount(privateKey as `0x${string}`);

  const publicClient = createPublicClient({
    chain: monadTestnet,
    transport: http(),
  });

  const walletClient = createWalletClient({
    account,
    chain: monadTestnet,
    transport: http(),
  });

  console.log(`Using account: ${account.address}`);

  // Load Artifacts
  const ledgerArtifact = JSON.parse(fs.readFileSync(path.join(process.cwd(), "artifacts/ProvenanceLedger.json"), "utf8"));
  const registryArtifact = JSON.parse(fs.readFileSync(path.join(process.cwd(), "artifacts/ProvenanceRegistry.json"), "utf8"));

  // 1. Deploy ProvenanceLedger
  console.log("Deploying ProvenanceLedger...");
  const ledgerHash = await walletClient.deployContract({
    abi: ledgerArtifact.abi,
    bytecode: ledgerArtifact.evm.bytecode.object,
    args: [account.address],
  });
  const ledgerReceipt = await publicClient.waitForTransactionReceipt({ hash: ledgerHash });
  const ledgerAddress = ledgerReceipt.contractAddress!;
  console.log(`✅ ProvenanceLedger deployed to: ${ledgerAddress}`);

  // 2. Deploy ProvenanceRegistry
  console.log("Deploying ProvenanceRegistry...");
  const registryHash = await walletClient.deployContract({
    abi: registryArtifact.abi,
    bytecode: registryArtifact.evm.bytecode.object,
    args: [ledgerAddress],
  });
  const registryReceipt = await publicClient.waitForTransactionReceipt({ hash: registryHash });
  const registryAddress = registryReceipt.contractAddress!;
  console.log(`✅ ProvenanceRegistry deployed to: ${registryAddress}`);

  // 3. Link Registry to Ledger
  console.log("Linking Registry to Ledger...");
  const { request } = await publicClient.simulateContract({
    account,
    address: ledgerAddress,
    abi: ledgerArtifact.abi,
    functionName: "setRegistryAddress",
    args: [registryAddress],
  });
  const linkHash = await walletClient.writeContract(request);
  await publicClient.waitForTransactionReceipt({ hash: linkHash });
  console.log("✅ Registry linked to Ledger");

  updateSettlement(ledgerAddress, registryAddress);
}

function mockDeployment() {
    const mockLedger = "0x4c0883a69102937d6231471b5dbb6204fe302702fd307ce2304598dcf3e346d1";
    const mockRegistry = "0x71C7656EC7ab88b098defB751B7401B5f6d147a3";
    console.log("💡 Simulation Mode: Mocking configuration outputs to public/settlement.json");
    updateSettlement(mockLedger, mockRegistry);
}

function updateSettlement(ledgerAddress: string, registryAddress: string) {
    const settlementPath = path.join(process.cwd(), "public/settlement.json");
    let settlementData: any = { contracts: {} };
    if (fs.existsSync(settlementPath)) {
        settlementData = JSON.parse(fs.readFileSync(settlementPath, "utf8"));
    }
    settlementData.contracts["Intelligence_Ledger"] = ledgerAddress;
    settlementData.contracts["Provenance_Registry"] = registryAddress;
    fs.writeFileSync(settlementPath, JSON.stringify(settlementData, null, 2));
    console.log(`✓ Configuration map synchronized in ${settlementPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
