const fs = require("fs");
const path = require("path");
const { ethers } = require("hardhat");

async function main() {
  const Factory = await ethers.getContractFactory("FlowStatePayout");
  const contract = await Factory.deploy();
  await contract.waitForDeployment();

  const fundTx = await contract.fundPool({ value: ethers.parseEther("1") });
  await fundTx.wait();

  const address = await contract.getAddress();
  const artifactPath = path.join(
    __dirname,
    "..",
    "artifacts",
    "contracts",
    "FlowStatePayout.sol",
    "FlowStatePayout.json"
  );
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  const outputPath = path.join(
    __dirname,
    "..",
    "..",
    "backend",
    "contract",
    "deployment.json"
  );

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify({ address, abi: artifact.abi }, null, 2));
  console.log(`FlowStatePayout deployed at ${address}`);
  console.log(`Pool balance: ${ethers.formatEther(await contract.poolBalance())} ETH`);
  console.log(`Deployment file: ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
