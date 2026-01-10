const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('RewardDistribution', function () {
  let token, rewards;
  let owner, distributor, contributor;

  beforeEach(async function () {
    [owner, distributor, contributor] = await ethers.getSigners();

    // Deploy token
    const NWUToken = await ethers.getContractFactory('NWUToken');
    token = await NWUToken.deploy();
    await token.waitForDeployment();
    const tokenAddress = await token.getAddress();

    // Deploy rewards contract
    const RewardDistribution = await ethers.getContractFactory('RewardDistribution');
    rewards = await RewardDistribution.deploy(tokenAddress);
    await rewards.waitForDeployment();
    const rewardsAddress = await rewards.getAddress();

    // Setup: add rewards contract as minter and fund it
    await token.addMinter(rewardsAddress);
    await token.transfer(rewardsAddress, ethers.parseEther('1000000'));
  });

  describe('Deployment', function () {
    it('Should set the token address', async function () {
      const tokenAddress = await token.getAddress();
      expect(await rewards.token()).to.equal(tokenAddress);
    });

    it('Should set owner as initial distributor', async function () {
      expect(await rewards.distributors(owner.address)).to.be.true;
    });
  });

  describe('Distributor Management', function () {
    it('Should allow owner to add distributors', async function () {
      await rewards.addDistributor(distributor.address);
      expect(await rewards.distributors(distributor.address)).to.be.true;
    });

    it('Should allow owner to remove distributors', async function () {
      await rewards.addDistributor(distributor.address);
      await rewards.removeDistributor(distributor.address);
      expect(await rewards.distributors(distributor.address)).to.be.false;
    });
  });

  describe('Reward Calculation', function () {
    it('Should calculate correct reward for quality score 70', async function () {
      const reward = await rewards.calculateReward(70);
      const baseReward = await rewards.BASE_REWARD();
      expect(reward).to.equal(baseReward);
    });

    it('Should calculate correct reward for quality score 100', async function () {
      const reward = await rewards.calculateReward(100);
      const baseReward = await rewards.BASE_REWARD();
      const expected = (baseReward * 100n) / 70n;
      expect(reward).to.equal(expected);
    });

    it('Should revert for quality score below minimum', async function () {
      await expect(rewards.calculateReward(69)).to.be.revertedWith('Quality score too low');
    });

    it('Should revert for invalid quality score', async function () {
      await expect(rewards.calculateReward(101)).to.be.revertedWith('Invalid quality score');
    });
  });

  describe('Allocate Rewards', function () {
    beforeEach(async function () {
      await rewards.addDistributor(distributor.address);
    });

    it('Should allow distributor to allocate rewards', async function () {
      const qualityScore = 85;
      await rewards.connect(distributor).allocateReward(contributor.address, qualityScore);

      const pending = await rewards.pendingRewards(contributor.address);
      expect(pending).to.be.gt(0);
    });

    it('Should not allow non-distributor to allocate', async function () {
      await expect(
        rewards.connect(contributor).allocateReward(contributor.address, 85)
      ).to.be.revertedWith('Not authorized distributor');
    });

    it('Should accumulate multiple rewards', async function () {
      await rewards.connect(distributor).allocateReward(contributor.address, 80);
      const firstReward = await rewards.pendingRewards(contributor.address);
      
      await rewards.connect(distributor).allocateReward(contributor.address, 90);
      const totalReward = await rewards.pendingRewards(contributor.address);
      
      expect(totalReward).to.be.gt(firstReward);
    });
  });

  describe('Claim Rewards', function () {
    beforeEach(async function () {
      await rewards.addDistributor(distributor.address);
      await rewards.connect(distributor).allocateReward(contributor.address, 85);
    });

    it('Should allow contributor to claim rewards', async function () {
      const pendingBefore = await rewards.pendingRewards(contributor.address);
      const balanceBefore = await token.balanceOf(contributor.address);

      await rewards.connect(contributor).claimRewards();

      const pendingAfter = await rewards.pendingRewards(contributor.address);
      const balanceAfter = await token.balanceOf(contributor.address);

      expect(pendingAfter).to.equal(0);
      expect(balanceAfter).to.equal(balanceBefore + pendingBefore);
    });

    it('Should not allow claiming with no rewards', async function () {
      await expect(
        rewards.connect(owner).claimRewards()
      ).to.be.revertedWith('No rewards to claim');
    });

    it('Should track claimed rewards', async function () {
      const pending = await rewards.pendingRewards(contributor.address);
      await rewards.connect(contributor).claimRewards();

      const claimed = await rewards.claimedRewards(contributor.address);
      expect(claimed).to.equal(pending);
    });

    it('Should update total distributed', async function () {
      const totalBefore = await rewards.totalDistributed();
      const pending = await rewards.pendingRewards(contributor.address);
      
      await rewards.connect(contributor).claimRewards();
      
      const totalAfter = await rewards.totalDistributed();
      expect(totalAfter).to.equal(totalBefore + pending);
    });
  });

  describe('Pause Functionality', function () {
    beforeEach(async function () {
      await rewards.addDistributor(distributor.address);
    });

    it('Should allow owner to pause', async function () {
      await rewards.pause();
      expect(await rewards.paused()).to.be.true;
    });

    it('Should not allow allocation when paused', async function () {
      await rewards.pause();
      await expect(
        rewards.connect(distributor).allocateReward(contributor.address, 85)
      ).to.be.reverted;
    });

    it('Should not allow claiming when paused', async function () {
      await rewards.connect(distributor).allocateReward(contributor.address, 85);
      await rewards.pause();
      
      await expect(
        rewards.connect(contributor).claimRewards()
      ).to.be.reverted;
    });
  });
});
