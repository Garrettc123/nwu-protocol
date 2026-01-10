const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('VerificationRegistry', function () {
  let registry;
  let owner, verifier, contributor;

  beforeEach(async function () {
    [owner, verifier, contributor] = await ethers.getSigners();

    const VerificationRegistry = await ethers.getContractFactory('VerificationRegistry');
    registry = await VerificationRegistry.deploy();
    await registry.waitForDeployment();
  });

  describe('Deployment', function () {
    it('Should set the owner as initial verifier', async function () {
      expect(await registry.verifiers(owner.address)).to.be.true;
    });
  });

  describe('Verifier Management', function () {
    it('Should allow owner to add verifiers', async function () {
      await registry.addVerifier(verifier.address);
      expect(await registry.verifiers(verifier.address)).to.be.true;
    });

    it('Should allow owner to remove verifiers', async function () {
      await registry.addVerifier(verifier.address);
      await registry.removeVerifier(verifier.address);
      expect(await registry.verifiers(verifier.address)).to.be.false;
    });

    it('Should not allow non-owner to add verifiers', async function () {
      await expect(
        registry.connect(verifier).addVerifier(contributor.address)
      ).to.be.reverted;
    });
  });

  describe('Record Verification', function () {
    const contributionId = ethers.keccak256(ethers.toUtf8Bytes('contribution1'));
    const ipfsHash = ethers.keccak256(ethers.toUtf8Bytes('QmTest'));
    const qualityScore = 85;

    beforeEach(async function () {
      await registry.addVerifier(verifier.address);
    });

    it('Should allow verifier to record verification', async function () {
      await registry.connect(verifier).recordVerification(
        contributionId,
        ipfsHash,
        qualityScore,
        contributor.address
      );

      const verification = await registry.verifications(contributionId);
      expect(verification.exists).to.be.true;
      expect(verification.qualityScore).to.equal(qualityScore);
      expect(verification.contributor).to.equal(contributor.address);
      expect(verification.verified).to.be.true; // Score >= 70
    });

    it('Should not allow non-verifier to record', async function () {
      await expect(
        registry.connect(contributor).recordVerification(
          contributionId,
          ipfsHash,
          qualityScore,
          contributor.address
        )
      ).to.be.revertedWith('Not authorized verifier');
    });

    it('Should mark as not verified if score is low', async function () {
      const lowScore = 60;
      await registry.connect(verifier).recordVerification(
        contributionId,
        ipfsHash,
        lowScore,
        contributor.address
      );

      const verification = await registry.verifications(contributionId);
      expect(verification.verified).to.be.false;
    });

    it('Should not allow duplicate verifications', async function () {
      await registry.connect(verifier).recordVerification(
        contributionId,
        ipfsHash,
        qualityScore,
        contributor.address
      );

      await expect(
        registry.connect(verifier).recordVerification(
          contributionId,
          ipfsHash,
          qualityScore,
          contributor.address
        )
      ).to.be.revertedWith('Verification already exists');
    });
  });

  describe('Get Verification', function () {
    const contributionId = ethers.keccak256(ethers.toUtf8Bytes('contribution2'));
    const ipfsHash = ethers.keccak256(ethers.toUtf8Bytes('QmTest2'));
    const qualityScore = 90;

    beforeEach(async function () {
      await registry.addVerifier(verifier.address);
      await registry.connect(verifier).recordVerification(
        contributionId,
        ipfsHash,
        qualityScore,
        contributor.address
      );
    });

    it('Should return verification details', async function () {
      const result = await registry.getVerification(contributionId);
      expect(result.qualityScore).to.equal(qualityScore);
      expect(result.contributor).to.equal(contributor.address);
      expect(result.verified).to.be.true;
    });

    it('Should track contributor verifications', async function () {
      const contributions = await registry.getContributorVerifications(contributor.address);
      expect(contributions.length).to.equal(1);
      expect(contributions[0]).to.equal(contributionId);
    });

    it('Should calculate contributor stats', async function () {
      const stats = await registry.getContributorStats(contributor.address);
      expect(stats.totalContributions).to.equal(1);
      expect(stats.verifiedContributions).to.equal(1);
      expect(stats.averageScore).to.equal(qualityScore);
    });
  });
});
