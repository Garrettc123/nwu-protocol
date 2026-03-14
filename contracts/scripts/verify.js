const hre = require('hardhat');
const fs = require('fs');
const path = require('path');

async function main() {
  const network = hre.network.name;
  console.log(`Verifying NWU Protocol contracts on Etherscan (${network})...`);

  // Load deployment addresses
  const deploymentsPath = path.join(__dirname, '..', 'deployments', `${network}.json`);
  if (!fs.existsSync(deploymentsPath)) {
    throw new Error(
      `No deployment found for network "${network}". ` +
        `Run deploy:${network} first to generate deployments/${network}.json.`
    );
  }

  const deployment = JSON.parse(fs.readFileSync(deploymentsPath, 'utf8'));
  const { NWUToken, VerificationRegistry, RewardDistribution } = deployment.contracts;

  console.log('\nVerifying NWUToken...');
  await hre.run('verify:verify', {
    address: NWUToken,
    constructorArguments: [],
  });
  console.log(`NWUToken verified: https://etherscan.io/address/${NWUToken}`);

  console.log('\nVerifying VerificationRegistry...');
  await hre.run('verify:verify', {
    address: VerificationRegistry,
    constructorArguments: [],
  });
  console.log(
    `VerificationRegistry verified: https://etherscan.io/address/${VerificationRegistry}`
  );

  console.log('\nVerifying RewardDistribution...');
  await hre.run('verify:verify', {
    address: RewardDistribution,
    constructorArguments: [NWUToken],
  });
  console.log(`RewardDistribution verified: https://etherscan.io/address/${RewardDistribution}`);

  console.log('\n=== Etherscan Verification Complete ===');
  console.log(`NWUToken:              https://etherscan.io/address/${NWUToken}`);
  console.log(`VerificationRegistry:  https://etherscan.io/address/${VerificationRegistry}`);
  console.log(`RewardDistribution:    https://etherscan.io/address/${RewardDistribution}`);
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
