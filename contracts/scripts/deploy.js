const hre = require('hardhat');

async function main() {
  console.log('Deploying NWU Protocol contracts...');

  // Deploy NWU Token
  const NWUToken = await hre.ethers.getContractFactory('NWUToken');
  const token = await NWUToken.deploy();
  await token.waitForDeployment();
  const tokenAddress = await token.getAddress();
  console.log(`NWUToken deployed to: ${tokenAddress}`);

  // Deploy Verification Registry
  const VerificationRegistry = await hre.ethers.getContractFactory('VerificationRegistry');
  const registry = await VerificationRegistry.deploy();
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();
  console.log(`VerificationRegistry deployed to: ${registryAddress}`);

  // Deploy Reward Distribution
  const RewardDistribution = await hre.ethers.getContractFactory('RewardDistribution');
  const rewards = await RewardDistribution.deploy(tokenAddress);
  await rewards.waitForDeployment();
  const rewardsAddress = await rewards.getAddress();
  console.log(`RewardDistribution deployed to: ${rewardsAddress}`);

  // Setup: Add reward contract as minter
  console.log('\nSetting up contracts...');
  await token.addMinter(rewardsAddress);
  console.log('✓ Reward contract added as minter');

  // Transfer tokens to reward contract
  const transferAmount = hre.ethers.parseEther('10000000'); // 10M tokens
  await token.transfer(rewardsAddress, transferAmount);
  console.log(`✓ Transferred ${hre.ethers.formatEther(transferAmount)} NWU to reward contract`);

  console.log('\n=== Deployment Summary ===');
  console.log(`NWUToken: ${tokenAddress}`);
  console.log(`VerificationRegistry: ${registryAddress}`);
  console.log(`RewardDistribution: ${rewardsAddress}`);
  console.log('\nDeployment complete!');
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
