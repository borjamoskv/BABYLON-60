import {
  alice,
  bob,
  deployer,
  dlmmCore,
  errors,
  generateBinFactors,
  sbtcUsdcPool,
  mockSbtcToken,
  mockUsdcToken,
  mockRandomToken,
} from "../helpers/helpers";

import { describe, it, expect, beforeEach } from 'vitest';
import { accounts } from '../helpers/clarigen-types'; 
import {
  cvToValue,
} from '@clarigen/core';
import { txErr, txOk, rovOk } from '@clarigen/test';



describe('DLMM Core Contract', () => {
  // Initialize expected bin steps before all tests that need them
  const initializeBinSteps = async () => {
    const expectedBinSteps = [1n, 5n, 10n, 20n, 25n];
    const currentBinSteps = rovOk(dlmmCore.getBinSteps());
    for (const binStep of expectedBinSteps) {
      if (!currentBinSteps.includes(binStep)) {
        const factors = generateBinFactors();
        txOk(dlmmCore.addBinStep(binStep, factors), deployer);
      }
    }
  };

  describe('Admin Management', () => {
    it('Deployer should be the only admin at deploy', async () => {
      const currentAdmins = rovOk(dlmmCore.getAdmins());
      expect(currentAdmins.length).toBe(1);
      expect(currentAdmins[0]).toBe(deployer);
    });

    describe('Adding Admin', () => { ///////////////////////////////////////////////////////////////////
      it('Should allow deployer to add new admin', async () => {
        const principal = alice;
        txOk(dlmmCore.addAdmin(principal), deployer);
        const admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        expect(admins[1]).toBe(principal);
      });

      it('Should allow new admins to add other new admins', async () => {
        const principal = alice;
        txOk(dlmmCore.addAdmin(principal), deployer);
        let admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        expect(admins[1]).toBe(principal);

        txOk(dlmmCore.addAdmin(bob), principal);
        admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(3);
        expect(admins[2]).toBe(bob);
      });

      it('Should prevent adding same admin twice', async () => {
        const principal = alice;
        txOk(dlmmCore.addAdmin(principal), deployer);
        let admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        expect(admins[1]).toBe(principal);
        const response = txErr(dlmmCore.addAdmin(principal), deployer);
        admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_ALREADY_ADMIN);
      });

      it('Should prevent adding more than 5 admins in total', async () => {
        const adminList = [
          accounts.wallet_1.address, accounts.wallet_2.address, accounts.wallet_3.address, accounts.wallet_4.address
        ];
        for (const principal of adminList) {
          txOk(dlmmCore.addAdmin(principal), deployer);
        }
      
        let admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(5);
        
        const response = txErr(dlmmCore.addAdmin(accounts.wallet_5.address), deployer);
        admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(5);
        expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_ADMIN_LIMIT_REACHED);
      });

      it('Should prevent non-admin from adding admin', async () => {
        const principal = alice;
        const response = txErr(dlmmCore.addAdmin(principal), bob);
        const admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(1);
        expect(admins.includes(principal)).toBeFalsy();
        expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_NOT_AUTHORIZED);
      });
    });

    describe('Removing Admin', () => { ///////////////////////////////////////////////////////////////////
      it('Should deny removal of deployer', async () => {
        const response = txErr(dlmmCore.removeAdmin(deployer), deployer);
        const admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(1);
        expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER);
      });
    
      it('Should allow removal of normal admins', async () => {
        txOk(dlmmCore.addAdmin(alice), deployer);
        let admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        txOk(dlmmCore.removeAdmin(alice), deployer);
        admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(1);
      });

      it('Should allow self-removal from admins', async () => {
        txOk(dlmmCore.addAdmin(alice), deployer);
        let admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        txOk(dlmmCore.removeAdmin(alice), alice);
        admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(1);
      });

      it('Should fail to remove principal which is not an admin', async () => {
        const response = txErr(dlmmCore.removeAdmin(alice), deployer);
        const admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(1);
        expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_ADMIN_NOT_IN_LIST);
      });

      it('Should deny removal of an admin by non-admins', async () => {
        txOk(dlmmCore.addAdmin(alice), deployer);
        let admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        const response = txErr(dlmmCore.removeAdmin(alice), bob);
        admins = rovOk(dlmmCore.getAdmins());
        expect(admins.length).toBe(2);
        expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_NOT_AUTHORIZED);
      });
    });
  });

  describe('Bin Step Management', () => { ///////////////////////////////////////////////////////////////////
    beforeEach(initializeBinSteps);

    it('Should allow admin to add valid bin step', async () => {
      const binStep = 100n;
      const factors = generateBinFactors();
      
      let binSteps = rovOk(dlmmCore.getBinSteps());
      expect(binSteps.length, "initial bin step list should have 5 elements").toBe(5);
      expect(binSteps).toStrictEqual([1n, 5n, 10n, 20n, 25n]);

      txOk(dlmmCore.addBinStep(binStep, factors), deployer);

      binSteps = rovOk(dlmmCore.getBinSteps());
      expect(binSteps.includes(binStep));

    });

    it('Should prevent adding duplicate bin step', async () => {
      const binStep = 1n; // This already exists in constants
      const factors = generateBinFactors();
      const response = txErr(dlmmCore.addBinStep(binStep, factors), deployer);
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_ALREADY_BIN_STEP);
    });

    it('Should prevent non-admin from adding bin step', async () => {
      const binStep = 200n;
      const factors = generateBinFactors();
      
      const response = txErr(dlmmCore.addBinStep(binStep, factors), alice);
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_NOT_AUTHORIZED);
    });

    it('Should prevent adding a bin-step with a factor element array without 1001 entries', async () => {
      const binStep = 200n;
      const factors = generateBinFactors(500);
      const response = txErr(dlmmCore.addBinStep(binStep, factors), deployer);
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_BIN_FACTORS_LENGTH);
    });

    it('Should prevent from adding a 0 bin step', async () => {
      const binStep = 0n;
      const factors = generateBinFactors();
      const response = txErr(dlmmCore.addBinStep(binStep, factors), deployer);
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_AMOUNT);
    });

    it.skip('Should prevent from adding a more than 1000 bin steps', async () => {
      const lastBinStep = 10000n;
      
      for (const binStep of generateBinFactors(995, 100n)) {
        txOk(dlmmCore.addBinStep(binStep, generateBinFactors()), deployer);
      }
      const response = txErr(dlmmCore.addBinStep(lastBinStep, generateBinFactors()), deployer);
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_BIN_STEP_LIMIT_REACHED);
    }, 1000000);

  });

  describe('Read-Only Functions', () => { ///////////////////////////////////////////////////////////////////
    beforeEach(initializeBinSteps);
    
    it('should return current admins list', async () => {
      const result = rovOk(dlmmCore.getAdmins());
      expect(result).toEqual([deployer]);
    });

    it('should return correct last pool id', async () => {
      const result = rovOk(dlmmCore.getLastPoolId());
      expect(result).toBe(0n);
    });

    it('should return correct bin steps', async () => {
      const result = rovOk(dlmmCore.getBinSteps());
      const expectedSteps = [1n, 5n, 10n, 20n, 25n];
      expect(result).toEqual(expectedSteps);
    });

    it('should return minimum shares values', async () => {
      const minBinResult = rovOk(dlmmCore.getMinimumBinShares());
      const minBurntResult = rovOk(dlmmCore.getMinimumBurntShares());
      
      expect(minBinResult).toBe(10000n);
      expect(minBurntResult).toBe(1000n);
    });

    it('should return public pool creation status', async () => {
      const result = rovOk(dlmmCore.getPublicPoolCreation());
      expect(result).toBe(false);
    });
  });

  describe('Utility Functions', () => {
    beforeEach(initializeBinSteps);
    
    it('should convert between signed and unsigned bin IDs', async () => {
      const testBinId = 250n;
      
      const signedResult = rovOk(dlmmCore.getSignedBinId(testBinId));
      const unsignedResult = rovOk(dlmmCore.getUnsignedBinId(testBinId - 500n)); // CENTER_BIN_ID offset
      
      expect(signedResult).toBe(testBinId - 500n);
      expect(unsignedResult).toBe(testBinId);
    });

    it('should calculate bin price correctly', async () => {
      // Ensure bin step 25 exists (should be initialized above)
      const initialPrice = 100000000n; // PRICE_SCALE_BPS
      const binStep = 25n;
      const binId = 0n;
      
      const result = rovOk(dlmmCore.getBinPrice(initialPrice, binStep, binId));
      expect(result).toBe(initialPrice);
    });

    it('should calculate liquidity value correctly', async () => {
      const xAmount = 1000000n;
      const yAmount = 2000000n;
      const binPrice = 1000000n;
      
      const result = rovOk(dlmmCore.getLiquidityValue(xAmount, yAmount, binPrice));
      expect(result).toBeDefined();
    });
  });

  describe('Settings Management', () => {
    beforeEach(initializeBinSteps);
    
    it('should allow admin to set public pool creation', async () => {
      txOk(dlmmCore.setPublicPoolCreation(true), deployer);
    });

    it('should allow admin to set minimum shares', async () => {
      const newMinBin = 15000n;
      const newMinBurnt = 1500n;
      
      txOk(dlmmCore.setMinimumShares(newMinBin, newMinBurnt), deployer);
    });

    it('should prevent non-admin from changing settings', async () => {
      const response = txErr(dlmmCore.setPublicPoolCreation(true), alice);
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_NOT_AUTHORIZED);
    });

    it('should succeed when creating pool with random X token (pool creation does not validate token whitelisting)', async () => {
      // Mint tokens for pool creation
      txOk(mockRandomToken.mint(10000000n, deployer), deployer);
      txOk(mockUsdcToken.mint(5000000000n, deployer), deployer);

      const response = txOk(dlmmCore.createPool(
        sbtcUsdcPool.identifier,           
        mockRandomToken.identifier, // Using random token
        mockUsdcToken.identifier,          
        10000000n,    // 0.1 BTC in active bin
        5000000000n,  // 5000 USDC in active bin  
        1000n,        // burn amount
        1000n, 3000n, // x fees (0.1% protocol, 0.3% provider)
        1000n, 3000n, // y fees (0.1% protocol, 0.3% provider)
        25n,          // bin step (25 basis points)
        900n,         // variable fees cooldown
        false,        // freeze variable fees manager
        null,         // dynamic-config (optional)
        deployer,     // fee address
        "https://bitflow.finance/dlmm", // uri
        true          // status
      ), deployer);
      
      expect(response).toBeDefined();
    });

    it('should succeed when creating pool with random Y token (pool creation does not validate token whitelisting)', async () => {
      // Mint tokens for pool creation
      txOk(mockSbtcToken.mint(10000000n, deployer), deployer);
      txOk(mockRandomToken.mint(5000000000n, deployer), deployer);

      const response = txOk(dlmmCore.createPool(
        sbtcUsdcPool.identifier,           
        mockSbtcToken.identifier,
        mockRandomToken.identifier, // Using random token        
        10000000n,    // 0.1 BTC in active bin
        5000000000n,  // 5000 USDC in active bin  
        1000n,        // burn amount
        1000n, 3000n, // x fees (0.1% protocol, 0.3% provider)
        1000n, 3000n, // y fees (0.1% protocol, 0.3% provider)
        25n,          // bin step (25 basis points)
        900n,         // variable fees cooldown
        false,        // freeze variable fees manager
        null,         // dynamic-config (optional)
        deployer,     // fee address
        "https://bitflow.finance/dlmm", // uri
        true          // status
      ), deployer);
      
      expect(response).toBeDefined();
    });
  });
});