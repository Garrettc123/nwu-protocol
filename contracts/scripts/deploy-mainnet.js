const hre = require('hardhat');
const fs = require('fs');
const path = require('path');

async function main() {
  const network = hre.network.name;
  if (network !== 'mainnet') {
    throw new Error(`Expected network "mainnet", got "${network}". Run with --network mainnet.`);
  }

  // Confirm deployer balance before proceeding
  const [deployer] = await hre.ethers.getSigners();
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log(`Deploying NWU Protocol contracts to mainnet...`);
  console.log(`Deployer: ${deployer.address}`);
  console.log(`Balance:  ${hre.ethers.formatEther(balance)} ETH`);

  if (balance === 0n) {
    throw new Error('Deployer account has no ETH. Fund the account before deploying.');
  }

  // Deploy NWU Token
  console.log('\nDeploying NWUToken...');
  const NWUToken = await hre.ethers.getContractFactory('NWUToken');
  const token = await NWUToken.deploy();
  await token.waitForDeployment();
  const tokenAddress = await token.getAddress();
  console.log(`NWUToken deployed to: ${tokenAddress}`);

  // Deploy Verification Registry
  console.log('\nDeploying VerificationRegistry...');
  const VerificationRegistry = await hre.ethers.getContractFactory('VerificationRegistry');
  const registry = await VerificationRegistry.deploy();
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();
  console.log(`VerificationRegistry deployed to: ${registryAddress}`);

  // Deploy Reward Distribution
  console.log('\nDeploying RewardDistribution...');
  const RewardDistribution = await hre.ethers.getContractFactory('RewardDistribution');
  const rewards = await RewardDistribution.deploy(tokenAddress);
  await rewards.waitForDeployment();
  const rewardsAddress = await rewards.getAddress();
  console.log(`RewardDistribution deployed to: ${rewardsAddress}`);

  // Setup: grant minting rights to reward contract
  console.log('\nConfiguring contracts...');
  await token.addMinter(rewardsAddress);
  console.log('Reward contract granted minter role');

  // Transfer initial token allocation to reward contract.
  // 10M NWU (10% of the 100M total supply) seeds the reward pool for contributor payouts.
  const transferAmount = hre.ethers.parseEther('10000000'); // 10M NWU
  await token.transfer(rewardsAddress, transferAmount);
  console.log(`Transferred ${hre.ethers.formatEther(transferAmount)} NWU to reward contract`);

  // Save deployment addresses for verification step
  const deployment = {
    network: 'mainnet',
    deployedAt: new Date().toISOString(),
    deployer: deployer.address,
    contracts: {
      NWUToken: tokenAddress,
      VerificationRegistry: registryAddress,
      RewardDistribution: rewardsAddress,
    },
  };

  const outputPath = path.join(__dirname, '..', 'deployments', 'mainnet.json');
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(deployment, null, 2));
  console.log(`\nDeployment addresses saved to deployments/mainnet.json`);

  console.log('\n=== Mainnet Deployment Summary ===');
  console.log(`NWUToken:              ${tokenAddress}`);
  console.log(`VerificationRegistry:  ${registryAddress}`);
  console.log(`RewardDistribution:    ${rewardsAddress}`);
  console.log('\nNext step: run `npm run verify:mainnet` to verify contracts on Etherscan.');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
