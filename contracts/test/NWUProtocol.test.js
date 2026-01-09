const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('NWU Protocol Contracts', function () {
  let token, registry, rewards;
  let owner, addr1, addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();

    // Deploy NWU Token
    const NWUToken = await ethers.getContractFactory('NWUToken');
    token = await NWUToken.deploy();
    await token.waitForDeployment();

    // Deploy Verification Registry
    const VerificationRegistry = await ethers.getContractFactory('VerificationRegistry');
    registry = await VerificationRegistry.deploy();
    await registry.waitForDeployment();

    // Deploy Reward Distribution
    const RewardDistribution = await ethers.getContractFactory('RewardDistribution');
    rewards = await RewardDistribution.deploy(await token.getAddress());
    await rewards.waitForDeployment();

    // Setup
    await token.addMinter(await rewards.getAddress());
    await token.transfer(await rewards.getAddress(), ethers.parseEther('1000000'));
  });

  describe('NWUToken', function () {
    it('Should have correct name and symbol', async function () {
      expect(await token.name()).to.equal('NWU Protocol Token');
      expect(await token.symbol()).to.equal('NWU');
    });

    it('Should mint initial supply to owner', async function () {
      const balance = await token.balanceOf(owner.address);
      expect(balance).to.be.gt(0);
    });

    it('Should allow authorized minters to mint', async function () {
      const rewardsAddress = await rewards.getAddress();
      await token.connect(owner).addMinter(rewardsAddress);

      const initialBalance = await token.balanceOf(addr1.address);
      await token.connect(owner).mint(addr1.address, ethers.parseEther('100'));
      const finalBalance = await token.balanceOf(addr1.address);

      expect(finalBalance - initialBalance).to.equal(ethers.parseEther('100'));
    });
  });

  describe('VerificationRegistry', function () {
    it('Should record verification', async function () {
      const contributionId = ethers.keccak256(ethers.toUtf8Bytes('contribution1'));
      const ipfsHash = ethers.keccak256(ethers.toUtf8Bytes('QmTest123'));

      await registry.connect(owner).recordVerification(contributionId, ipfsHash, 85, addr1.address);

      const verification = await registry.getVerification(contributionId);
      expect(verification.qualityScore).to.equal(85);
      expect(verification.contributor).to.equal(addr1.address);
      expect(verification.verified).to.equal(true);
    });

    it('Should get contributor stats', async function () {
      const contributionId1 = ethers.keccak256(ethers.toUtf8Bytes('contribution1'));
      const contributionId2 = ethers.keccak256(ethers.toUtf8Bytes('contribution2'));
      const ipfsHash = ethers.keccak256(ethers.toUtf8Bytes('QmTest'));

      await registry.recordVerification(contributionId1, ipfsHash, 85, addr1.address);
      await registry.recordVerification(contributionId2, ipfsHash, 75, addr1.address);

      const stats = await registry.getContributorStats(addr1.address);
      expect(stats.totalContributions).to.equal(2);
      expect(stats.verifiedContributions).to.equal(2);
      expect(stats.averageScore).to.equal(80);
    });
  });

  describe('RewardDistribution', function () {
    it('Should calculate reward correctly', async function () {
      const reward70 = await rewards.calculateReward(70);
      const reward100 = await rewards.calculateReward(100);

      expect(reward70).to.equal(ethers.parseEther('100'));
      expect(reward100).to.be.gt(reward70);
    });

    it('Should allocate and claim rewards', async function () {
      await rewards.addDistributor(owner.address);
      await rewards.allocateReward(addr1.address, 85);

      const rewardInfo = await rewards.getRewardInfo(addr1.address);
      expect(rewardInfo.pending).to.be.gt(0);

      const initialBalance = await token.balanceOf(addr1.address);
      await rewards.connect(addr1).claimRewards();
      const finalBalance = await token.balanceOf(addr1.address);

      expect(finalBalance).to.be.gt(initialBalance);
    });
  });
});
