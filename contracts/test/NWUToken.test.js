const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('NWUToken', function () {
  let token;
  let owner, addr1, addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();

    const NWUToken = await ethers.getContractFactory('NWUToken');
    token = await NWUToken.deploy();
    await token.waitForDeployment();
  });

  describe('Deployment', function () {
    it('Should set the right owner', async function () {
      expect(await token.owner()).to.equal(owner.address);
    });

    it('Should assign the initial supply to the owner', async function () {
      const ownerBalance = await token.balanceOf(owner.address);
      const initialSupply = await token.INITIAL_SUPPLY();
      expect(ownerBalance).to.equal(initialSupply);
    });

    it('Should have correct name and symbol', async function () {
      expect(await token.name()).to.equal('NWU Protocol Token');
      expect(await token.symbol()).to.equal('NWU');
    });
  });

  describe('Minting', function () {
    it('Should allow owner to add minters', async function () {
      await token.addMinter(addr1.address);
      expect(await token.minters(addr1.address)).to.be.true;
    });

    it('Should allow authorized minters to mint', async function () {
      await token.addMinter(addr1.address);
      const mintAmount = ethers.parseEther('1000');
      
      await token.connect(addr1).mint(addr2.address, mintAmount);
      expect(await token.balanceOf(addr2.address)).to.equal(mintAmount);
    });

    it('Should not allow non-minters to mint', async function () {
      const mintAmount = ethers.parseEther('1000');
      await expect(
        token.connect(addr1).mint(addr2.address, mintAmount)
      ).to.be.revertedWith('Not authorized to mint');
    });

    it('Should not exceed max supply', async function () {
      await token.addMinter(addr1.address);
      const maxSupply = await token.MAX_SUPPLY();
      const currentSupply = await token.totalSupply();
      const excessAmount = maxSupply - currentSupply + ethers.parseEther('1');
      
      await expect(
        token.connect(addr1).mint(addr2.address, excessAmount)
      ).to.be.revertedWith('Exceeds max supply');
    });
  });

  describe('Burning', function () {
    it('Should allow users to burn their tokens', async function () {
      const burnAmount = ethers.parseEther('1000');
      const initialBalance = await token.balanceOf(owner.address);
      
      await token.burn(burnAmount);
      const finalBalance = await token.balanceOf(owner.address);
      
      expect(finalBalance).to.equal(initialBalance - burnAmount);
    });
  });

  describe('Pause functionality', function () {
    it('Should allow owner to pause', async function () {
      await token.pause();
      expect(await token.paused()).to.be.true;
    });

    it('Should not allow transfers when paused', async function () {
      await token.pause();
      await expect(
        token.transfer(addr1.address, ethers.parseEther('100'))
      ).to.be.reverted;
    });

    it('Should allow owner to unpause', async function () {
      await token.pause();
      await token.unpause();
      expect(await token.paused()).to.be.false;
    });
  });
});
