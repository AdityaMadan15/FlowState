const fs = require("fs");
const path = require("path");
const { ethers } = require("hardhat");

async function main() {
  const deploymentPath = path.join(__dirname, "..", "..", "backend", "contract", "deployment.json");
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  const [owner, worker] = await ethers.getSigners();
  const before = await ethers.provider.getBalance(worker.address);
  const contract = new ethers.Contract(deployment.address, deployment.abi, owner);
  const tx = await contract.triggerPayout(worker.address);
  const receipt = await tx.wait();
  const after = await ethers.provider.getBalance(worker.address);
  const received = after - before;
  if (received !== ethers.parseEther("0.0005")) {
    throw new Error(`Expected 0.0005 ETH, received ${ethers.formatEther(received)} ETH`);
  }
  console.log(`Account #1 received 0.0005 ETH in transaction ${receipt.hash}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
