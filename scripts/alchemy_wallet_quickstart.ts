import { createSmartWalletClient, alchemyWalletTransport } from "@alchemy/wallet-apis";
import { arbitrumSepolia } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import { zeroAddress } from "viem";
import "dotenv/config";

async function main() {
  const apiKey = process.env.ALCHEMY_API_KEY;
  const privateKey = process.env.PRIVATE_KEY || process.env.DEPLOYER_PRIVATE_KEY || process.env.APPRAISER_PRIVATE_KEY;
  const policyId = process.env.ALCHEMY_POLICY_ID;

  if (!apiKey || !privateKey || !policyId) {
    console.log("⚠️ Missing ALCHEMY_API_KEY, PRIVATE_KEY/DEPLOYER_PRIVATE_KEY, or ALCHEMY_POLICY_ID.");
    console.log("Running in simulation/mock mode...");
    mockRun();
    return;
  }

  console.log("🚀 Creating Alchemy Smart Wallet Client...");
  const client = createSmartWalletClient({
    transport: alchemyWalletTransport({
      apiKey,
    }),
    chain: arbitrumSepolia,
    signer: privateKeyToAccount(privateKey as `0x${string}`),
    paymaster: {
      policyId,
    },
  });

  console.log("💸 Sending sponsored transaction (EIP-7702)...");
  try {
    const { id } = await client.sendCalls({
      calls: [{ to: zeroAddress, value: BigInt(0) }],
    });

    console.log(`⏳ Waiting for transaction confirmation... Call ID: ${id}`);
    const status = await client.waitForCallsStatus({ id });
    console.log(`✅ Call status: ${status.status}`);
  } catch (error) {
    console.error("❌ Failed to send transaction:", error);
  }
}

function mockRun() {
  console.log("\n--- [Simulation Mode Run] ---");
  const mockCallId = "0x89abcdef1234567890abcdef1234567890abcdef1234567890abcdef12345678";
  console.log(`Mock Call ID: ${mockCallId}`);
  console.log("Mock Status: confirmed");
  console.log("-------------------------------\n");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
