// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {ERC20Permit, ERC20} from "openzeppelin-contracts/contracts/token/ERC20/extensions/ERC20Permit.sol";
import {IERC165} from "openzeppelin-contracts/contracts/utils/introspection/IERC165.sol";
import {IAccessControl} from "openzeppelin-contracts/contracts/access/IAccessControl.sol";
import {Pausable} from "openzeppelin-contracts/contracts/utils/Pausable.sol";
import {IERC20Errors} from "openzeppelin-contracts/contracts/interfaces/draft-IERC6093.sol";
import {Test} from "forge-std/Test.sol";
import {Staking} from "../src/Staking.sol";
import {IStakingV1} from "../src/interfaces/IStakingV1.sol";
import {IMigratorV1} from "../src/interfaces/IMigratorV1.sol";
import {IMigratorReceiverV2} from "../src/interfaces/IMigratorReceiverV2.sol";

contract Token is ERC20Permit {
    constructor() ERC20Permit("TestToken") ERC20("TestToken", "TTKN") {}
}

contract UnsupportedToken is ERC20Permit {
    constructor() ERC20Permit("UnsupportedToken") ERC20("UnsupportedToken", "UTKN") {}
}

contract StakingTest is Test {
    Staking public staking;

    address public admin = address(2);
    address public manager = address(3);
    address public migrator = address(4);
    address public pauser = address(5);
    address public alice = address(6);
    address public bob = address(7);
    uint256 public charliePrivateKey = 0xca51;
    address public charlie = vm.addr(charliePrivateKey);

    Token public token;
    UnsupportedToken public unsupportedToken;

    function setUp() public {
        token = new Token();
        unsupportedToken = new UnsupportedToken();
        staking = new Staking(admin, manager, pauser, address(token));

        vm.prank(admin);
        staking.grantRole(keccak256("MIGRATOR"), migrator);
    }

    function test_Setup_Constructor() public view {
        assertEq(staking.owner(), admin);
        assertEq(staking.hasRole(keccak256("MANAGER"), manager), true);
        assertEq(staking.hasRole(keccak256("PAUSER"), pauser), true);
        assertEq(staking.hasRole(keccak256("MANAGER"), pauser), false);
        assertEq(staking.hasRole(keccak256("PAUSER"), manager), false);
        assertEq(address(staking.TOKEN()), address(token));
    }

    function test_Setup_AddStakingPeriod() public {
        vm.startPrank(manager);
        uint8 index0 = staking.addStakingPeriod(50 ether, 20, 10, 5000, true);
        assertEq(index0, 0);
        uint8 index1 = staking.addStakingPeriod(100 ether, 100, 10, 10000, false);
        assertEq(index1, 1);
        vm.stopPrank();
    }

    function test_Setup_RevertWhen_AddStakingPeriodWithZeroStakingDuration() public {
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakingDurationCannotBeZero.selector));
        addStakingPeriodByManager(50 ether, 0, 10, 5000, true);
    }

    function test_Setup_RevertWhen_AddStakingPeriodWithZeroUnlockDuration() public {
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.UnlockDurationCannotBeZero.selector));
        addStakingPeriodByManager(50 ether, 100, 0, 5000, true);
    }

    function test_Setup_RevertWhen_AddStakingPeriodsOverTheLimit() public {
        uint256 maxStakingPeriods = 256; // capacity of uint8

        for (uint256 i = 0; i < maxStakingPeriods; i++) {
            addStakingPeriodByManager(50 ether + i, 20, 10, 5000, true);
        }
        assertEq(staking.getStakingPeriods().length, maxStakingPeriods);

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.MaxStakingPeriodsReached.selector));
        addStakingPeriodByManager(50 ether, 20, 10, 5000, true);
    }

    function test_Setup_RevertWhen_UnauthorizedAddStakingPeriod() public {
        vm.expectRevert(
            abi.encodeWithSelector(
                IAccessControl.AccessControlUnauthorizedAccount.selector, pauser, staking.MANAGER_ROLE()
            )
        );
        vm.prank(pauser);
        staking.addStakingPeriod(50 ether, 20, 10, 5000, true);
    }

    function test_Setup_UpdateStakingPeriod() public {
        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        vm.prank(manager);
        staking.updateStakingPeriod(periodIndex, 100 ether, 100, 20, 10000, false);

        Staking.StakingPeriod[] memory stakingPeriods = staking.getStakingPeriods();
        assertEq(stakingPeriods[0].cap, 100 ether);
        assertEq(stakingPeriods[0].capUsed, 0);
        assertEq(stakingPeriods[0].stakingDurationSeconds, 100);
        assertEq(stakingPeriods[0].unlockDurationSeconds, 20);
        assertEq(stakingPeriods[0].aprBps, 10000);
        assertEq(stakingPeriods[0].isActive, false);
    }

    function test_Setup_UpdateSomePropsStakingPeriod() public {
        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        vm.prank(manager);
        staking.updateStakingPeriod(periodIndex, 50 ether, 100, 10, 10000, true);

        Staking.StakingPeriod[] memory stakingPeriods = staking.getStakingPeriods();
        assertEq(stakingPeriods[0].cap, 50 ether);
        assertEq(stakingPeriods[0].capUsed, 0);
        assertEq(stakingPeriods[0].stakingDurationSeconds, 100);
        assertEq(stakingPeriods[0].unlockDurationSeconds, 10);
        assertEq(stakingPeriods[0].aprBps, 10000);
        assertEq(stakingPeriods[0].isActive, true);
    }

    function test_Setup_RevertWhen_UpdateStakingPeriodWithZeroStakingDuration() public {
        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakingDurationCannotBeZero.selector));
        vm.prank(manager);
        staking.updateStakingPeriod(periodIndex, 50 ether, 0, 10, 5000, true);
    }

    function test_Setup_RevertWhen_UpdateStakingPeriodWithZeroUnlockDuration() public {
        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.UnlockDurationCannotBeZero.selector));
        vm.prank(manager);
        staking.updateStakingPeriod(periodIndex, 50 ether, 100, 0, 5000, true);
    }

    function test_Setup_RevertWhen_UnauthorizedUpdateStakingPeriod() public {
        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        vm.expectRevert(
            abi.encodeWithSelector(
                IAccessControl.AccessControlUnauthorizedAccount.selector, alice, staking.MANAGER_ROLE()
            )
        );
        vm.prank(alice);
        staking.updateStakingPeriod(periodIndex, 50 ether, 20, 10, 5000, true);
    }

    function testFuzz_Setup_RevertWhen_UpdateNonExistingStakingPeriod(uint8 index) public {
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.PeriodNotFound.selector));
        vm.prank(manager);
        staking.updateStakingPeriod(index, 50 ether, 20, 10, 5000, true);
    }

    function test_Staking_GetStakingPeriods() public {
        uint8 period0Index = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);
        uint8 period1Index = addStakingPeriodByManager(10 ether, 10, 5, 1000, false);

        assertEq(period0Index, 0);
        assertEq(period1Index, 1);

        Staking.StakingPeriod[] memory stakingPeriods = staking.getStakingPeriods();
        assertEq(stakingPeriods.length, 2);
        assertEq(stakingPeriods[0].cap, 50 ether);
        assertEq(stakingPeriods[0].stakingDurationSeconds, 20);
        assertEq(stakingPeriods[0].unlockDurationSeconds, 10);
        assertEq(stakingPeriods[0].aprBps, 5000);
        assertEq(stakingPeriods[0].isActive, true);
        assertEq(stakingPeriods[1].cap, 10 ether);
        assertEq(stakingPeriods[1].stakingDurationSeconds, 10);
        assertEq(stakingPeriods[1].unlockDurationSeconds, 5);
        assertEq(stakingPeriods[1].aprBps, 1000);
        assertEq(stakingPeriods[1].isActive, false);

        Staking.StakingPeriod memory stakingPeriod0 = staking.getStakingPeriod(period0Index);
        assertEq(stakingPeriod0.cap, 50 ether);
        assertEq(stakingPeriod0.stakingDurationSeconds, 20);
        assertEq(stakingPeriod0.unlockDurationSeconds, 10);
        assertEq(stakingPeriod0.aprBps, 5000);
        assertEq(stakingPeriod0.isActive, true);

        Staking.StakingPeriod memory stakingPeriod1 = staking.getStakingPeriod(period1Index);
        assertEq(stakingPeriod1.cap, 10 ether);
        assertEq(stakingPeriod1.stakingDurationSeconds, 10);
        assertEq(stakingPeriod1.unlockDurationSeconds, 5);
        assertEq(stakingPeriod1.aprBps, 1000);
        assertEq(stakingPeriod1.isActive, false);
    }

    function test_Staking_RevertWhen_GetNonExistingStakingPeriod() public {
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.PeriodNotFound.selector));
        staking.getStakingPeriod(0);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);
        uint8 nextPeriodIndex = periodIndex + 1;

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.PeriodNotFound.selector));
        staking.getStakingPeriod(nextPeriodIndex);
    }

    function test_Staking_Stake() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);

        uint256 aliceReward = calculateReward(10 ether, 20, 5000);
        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Staked(alice, periodIndex, address(0), 0, 10 ether, aliceReward);
        stake(alice, periodIndex, 10 ether, 20, 5, 5000, address(0));

        Staking.UserStake[] memory aliceStakes = staking.getUserStakes(alice);
        assertEq(aliceStakes.length, 1);
        assertEq(aliceStakes[0].amount, 10 ether);
        assertEq(token.balanceOf(address(staking)), 1000 ether + 10 ether);
    }

    function test_Staking_StakeWithReferer() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);

        uint256 aliceReward = calculateReward(10 ether, 20, 5000);
        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Staked(alice, periodIndex, bob, 0, 10 ether, aliceReward);
        stake(alice, periodIndex, 10 ether, 20, 5, 5000, bob);

        Staking.UserStake[] memory aliceStakes = staking.getUserStakes(alice);
        assertEq(aliceStakes.length, 1);
        assertEq(aliceStakes[0].amount, 10 ether);
        assertEq(token.balanceOf(address(staking)), 1000 ether + 10 ether);
    }

    function test_Staking_StakeIncreaseCapUsed() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 40 ether);

        stake(alice, periodIndex, 10 ether, 20, 5, 5000, address(0));
        IStakingV1.StakingPeriod memory stakingPeriod1 = staking.getStakingPeriod(periodIndex);
        assertEq(stakingPeriod1.capUsed, 10 ether);

        stake(alice, periodIndex, 5 ether, 20, 5, 5000, address(0));
        IStakingV1.StakingPeriod memory stakingPeriod2 = staking.getStakingPeriod(periodIndex);
        assertEq(stakingPeriod2.capUsed, 10 ether + 5 ether);
    }

    function test_Staking_RevertWhen_InsufficientAllowance() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 5 ether);
        vm.expectRevert(
            abi.encodeWithSelector(
                IERC20Errors.ERC20InsufficientAllowance.selector, address(staking), 5 ether, 10 ether
            )
        );
        stake(alice, periodIndex, 10 ether, 20, 5, 5000, address(0));
    }

    function testFuzz_Staking_RevertWhen_NonExistingPeriod(uint8 index) public {
        deal(address(token), alice, 100 ether);

        vm.prank(alice);
        token.approve(address(staking), 5 ether);
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.PeriodNotFound.selector));
        stake(alice, index, 10 ether, 0, 0, 0, address(0));
    }

    function test_Staking_RevertWhen_StakingAmountIsZero() public {
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.CannotStakeZero.selector));
        stake(alice, periodIndex, 0, 20, 5, 5000, address(0));
    }

    function test_Staking_RevertWhen_StakingPeriodIsInactive() public {
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, false);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakingPeriodInactive.selector, periodIndex));
        stake(alice, periodIndex, 1 ether, 20, 5, 5000, address(0));
    }

    function test_Staking_RevertWhen_StakingPeriodStakingDurationMoreThanExpected() public {
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 21, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);
        vm.expectRevert(
            abi.encodeWithSelector(IStakingV1.StakingPeriodStakingDurationDiffer.selector, periodIndex, 20, 21)
        );
        stake(alice, periodIndex, 1 ether, 20, 5, 5000, address(0));
    }

    function test_Staking_RevertWhen_StakingPeriodUnlockDurationMoreThanExpected() public {
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 6, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);
        vm.expectRevert(
            abi.encodeWithSelector(IStakingV1.StakingPeriodUnlockDurationDiffer.selector, periodIndex, 5, 6)
        );
        stake(alice, periodIndex, 1 ether, 20, 5, 5000, address(0));
    }

    function test_Staking_RevertWhen_StakingPeriodAprLessThanExpected() public {
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 4999, true);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakingPeriodAprDiffer.selector, periodIndex, 5000, 4999));
        stake(alice, periodIndex, 1 ether, 20, 5, 5000, address(0));
    }

    function test_Staking_RevertWhen_StakingOverCapSingleStake() public {
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 50 ether + 1);
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakingCapReached.selector, 50 ether));
        stake(alice, periodIndex, 50 ether + 1, 20, 5, 5000, address(0));
    }

    function test_Staking_RevertWhen_StakingOverCapSeveralStakes() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);
        deal(address(token), bob, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 5, 5000, true);

        vm.prank(alice);
        token.approve(address(staking), 26 ether);
        stake(alice, periodIndex, 26 ether, 20, 5, 5000, address(0));

        vm.prank(bob);
        token.approve(address(staking), 25 ether);
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakingCapReached.selector, 50 ether));
        stake(bob, periodIndex, 25 ether, 20, 5, 5000, address(0));
    }

    function test_Staking_RevertWhen_NotEnoughRewardBalance() public {
        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 20, 5000, true);

        uint256 aliceReward = calculateReward(10 ether, 10 days, 5000);

        deal(address(token), address(staking), aliceReward - 1);
        deal(address(token), alice, 100 ether);

        vm.prank(alice);
        token.approve(address(staking), 10 ether);
        vm.expectRevert(
            abi.encodeWithSelector(IStakingV1.NotEnoughContractBalance.selector, token, aliceReward - 1, aliceReward)
        );
        stake(alice, periodIndex, 10 ether, 10 days, 20, 5000, address(0));
    }

    function test_Staking_MultipleStakes() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        uint256 maxStakesPerUser = staking.MAX_STAKES_PER_USER();

        vm.prank(alice);
        token.approve(address(staking), 20 ether);
        for (uint256 i = 0; i < maxStakesPerUser; i++) {
            uint256 amount = 100 gwei + i;
            uint256 aliceReward = calculateReward(amount, 20, 5000);
            vm.expectEmit(true, true, true, true);
            assertLe(i, maxStakesPerUser);
            // casting to 'uint8' is safe because overflow checked in row above
            // forge-lint: disable-next-line(unsafe-typecast)
            emit IStakingV1.Staked(alice, periodIndex, address(0), uint8(i), amount, aliceReward);
            stake(alice, periodIndex, amount, 20, 10, 5000, address(0));
        }

        Staking.UserStake[] memory aliceStakes = staking.getUserStakes(alice);
        aliceStakes.length;
        assertEq(aliceStakes.length, maxStakesPerUser);
    }

    function test_Staking_RevertWhen_MultipleStakesOverTheLimit() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        uint256 maxStakesPerUser = staking.MAX_STAKES_PER_USER();

        vm.prank(alice);
        token.approve(address(staking), 20 ether);
        for (uint256 i = 0; i < maxStakesPerUser; i++) {
            stake(alice, periodIndex, 100 gwei + i, 20, 10, 5000, address(0));
        }

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.MaxUserStakesReached.selector, maxStakesPerUser));
        stake(alice, periodIndex, 500 gwei, 20, 10, 5000, address(0));

        Staking.UserStake[] memory aliceStakes = staking.getUserStakes(alice);
        assertEq(aliceStakes.length, maxStakesPerUser);
    }

    function test_Staking_StakeWithPermit() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), charlie, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        uint256 deadline = block.timestamp + 1 hours;
        (uint8 v, bytes32 r, bytes32 s) = signCharliePermit(10 ether, deadline);

        uint256 charlieReward = calculateReward(10 ether, 20, 5000);
        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Staked(charlie, periodIndex, address(0), 0, 10 ether, charlieReward);
        stakeWithPermit(charlie, periodIndex, 10 ether, 20, 10, 5000, address(0), deadline, v, r, s);

        Staking.UserStake[] memory charlieStakes = staking.getUserStakes(charlie);
        assertEq(charlieStakes.length, 1);
        assertEq(charlieStakes[0].amount, 10 ether);
        assertEq(token.balanceOf(charlie), 90 ether);
        assertEq(token.balanceOf(address(staking)), 1000 ether + 10 ether);
    }

    function test_Staking_StakeWithPermitWithReferer() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), charlie, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        uint256 deadline = block.timestamp + 1 hours;
        (uint8 v, bytes32 r, bytes32 s) = signCharliePermit(10 ether, deadline);

        uint256 charlieReward = calculateReward(10 ether, 20, 5000);
        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Staked(charlie, periodIndex, bob, 0, 10 ether, charlieReward);
        stakeWithPermit(charlie, periodIndex, 10 ether, 20, 10, 5000, bob, deadline, v, r, s);

        Staking.UserStake[] memory charlieStakes = staking.getUserStakes(charlie);
        assertEq(charlieStakes.length, 1);
        assertEq(charlieStakes[0].amount, 10 ether);
        assertEq(token.balanceOf(charlie), 90 ether);
        assertEq(token.balanceOf(address(staking)), 1000 ether + 10 ether);
    }

    function test_Staking_RevertWhen_ReuseSamePermitSignature() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), charlie, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        uint256 deadline = block.timestamp + 1 hours;
        (uint8 v, bytes32 r, bytes32 s) = signCharliePermit(10 ether, deadline);

        stakeWithPermit(charlie, periodIndex, 10 ether, 20, 10, 5000, address(0), deadline, v, r, s);

        vm.expectRevert(
            abi.encodeWithSelector(IERC20Errors.ERC20InsufficientAllowance.selector, address(staking), 0, 10 ether)
        );
        stakeWithPermit(charlie, periodIndex, 10 ether, 20, 10, 5000, address(0), deadline, v, r, s);
    }

    function test_Staking_RevertWhen_DifferentPersonSignature() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), charlie, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        uint256 deadline = block.timestamp + 1 hours;
        (uint8 v, bytes32 r, bytes32 s) = signCharliePermit(10 ether, deadline);

        vm.expectRevert(
            abi.encodeWithSelector(IERC20Errors.ERC20InsufficientAllowance.selector, address(staking), 0, 10 ether)
        );
        stakeWithPermit(alice, periodIndex, 10 ether, 20, 10, 5000, address(0), deadline, v, r, s);
    }

    function test_Staking_RevertWhen_PermitExpired() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), charlie, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);

        uint256 deadline = block.timestamp + 1 hours;
        (uint8 v, bytes32 r, bytes32 s) = signCharliePermit(10 ether, deadline);

        vm.warp(block.timestamp + 2 hours);

        vm.expectRevert(
            abi.encodeWithSelector(IERC20Errors.ERC20InsufficientAllowance.selector, address(staking), 0, 10 ether)
        );
        stakeWithPermit(charlie, periodIndex, 10 ether, 20, 10, 5000, address(0), deadline, v, r, s);
    }

    function test_Staking_GetUserStake() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);
        deal(address(token), bob, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);
        approveAndStake(alice, periodIndex, 7 ether, 20, 10, 5000, address(0));
        approveAndStake(bob, periodIndex, 3 ether, 20, 10, 5000, address(0));
        approveAndStake(alice, periodIndex, 10 ether, 20, 10, 5000, address(0));

        Staking.UserStake[] memory aliceStakes = staking.getUserStakes(alice);
        assertEq(aliceStakes.length, 2);
        assertEq(aliceStakes[0].amount, 7 ether);
        assertEq(aliceStakes[1].amount, 10 ether);

        Staking.UserStake[] memory bobStakes = staking.getUserStakes(bob);
        assertEq(bobStakes.length, 1);
        assertEq(bobStakes[0].amount, 3 ether);

        Staking.UserStake memory aliceStake0 = staking.getUserStake(alice, 0);
        assertEq(aliceStake0.amount, 7 ether);

        Staking.UserStake memory aliceStake1 = staking.getUserStake(alice, 1);
        assertEq(aliceStake1.amount, 10 ether);

        Staking.UserStake memory bobStake0 = staking.getUserStake(bob, 0);
        assertEq(bobStake0.amount, 3 ether);
    }

    function test_Staking_RevertWhen_GetNonExistingUserStake() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);
        approveAndStake(alice, periodIndex, 4 ether, 20, 10, 5000, address(0));

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakeNotFound.selector));
        staking.getUserStake(alice, periodIndex + 1);
    }

    function test_Staking_WithdrawAfterLinearUnlock() public {
        deal(address(token), address(staking), 1000 ether);
        uint256 initialAliceBalance = 100 ether;
        deal(address(token), alice, initialAliceBalance);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 1 days, 5000, true);
        uint8 stakeIndex = approveAndStake(alice, periodIndex, 10 ether, 10 days, 1 days, 5000, address(0));

        vm.warp(block.timestamp + 10 days + 1 days + 1 seconds);

        uint256 reward = calculateReward(10 ether, 10 days, 5000);

        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Withdrawn(alice, stakeIndex, 10 ether, reward);
        vm.prank(alice);
        uint256 withdrawn = staking.withdraw(stakeIndex);
        assertEq(withdrawn, 10 ether + reward);

        uint256 expectedAliceBalance = initialAliceBalance + reward;
        assertEq(token.balanceOf(alice), expectedAliceBalance);
        assertEq(token.balanceOf(address(staking)), 1000 ether - reward);
    }

    function test_Staking_WithdrawDuringLinearUnlock() public {
        deal(address(token), address(staking), 1000 ether);
        uint256 initialAliceBalance = 100 ether;
        deal(address(token), alice, initialAliceBalance);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 3 days, 5000, true);
        uint8 stakeIndex = approveAndStake(alice, periodIndex, 10 ether, 10 days, 3 days, 5000, address(0));

        uint256 claimableBefore = staking.getClaimable(alice, stakeIndex);
        assertEq(claimableBefore, 0);

        vm.warp(block.timestamp + 10 days + 1 days);

        uint256 totalReward = calculateReward(10 ether, 10 days, 5000);

        uint256 accruedAmount = uint256(10 ether * 1 days) / 3 days;
        uint256 accruedReward = uint256(totalReward * 1 days) / 3 days;

        uint256 claimableStep1 = staking.getClaimable(alice, stakeIndex);
        assertEq(claimableStep1, accruedAmount + accruedReward);

        vm.startPrank(alice);
        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Withdrawn(alice, stakeIndex, accruedAmount, accruedReward);
        uint256 withdrawn1 = staking.withdraw(stakeIndex);
        assertEq(withdrawn1, claimableStep1);

        uint256 expectedAliceBalance = initialAliceBalance - 10 ether + accruedAmount + accruedReward;
        assertEq(token.balanceOf(alice), expectedAliceBalance);

        vm.warp(block.timestamp + 2 days + 1);

        uint256 claimableStep2 = staking.getClaimable(alice, stakeIndex);
        assertEq(claimableStep2, 10 ether - accruedAmount + totalReward - accruedReward);

        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Withdrawn(alice, stakeIndex, 10 ether - accruedAmount, totalReward - accruedReward);
        uint256 withdrawn2 = staking.withdraw(stakeIndex);
        assertEq(withdrawn2, claimableStep2);
        vm.stopPrank();

        assertEq(token.balanceOf(alice), initialAliceBalance + totalReward);
        assertEq(token.balanceOf(address(staking)), 1000 ether - totalReward);

        uint256 claimableAfter = staking.getClaimable(alice, stakeIndex);
        assertEq(claimableAfter, 0);
    }

    function test_Staking_RevertWhen_AlreadyWithdrawn() public {
        deal(address(token), address(staking), 1000 ether);
        uint256 initialAliceBalance = 100 ether;
        deal(address(token), alice, initialAliceBalance);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 1 days, 5000, true);
        uint8 stakeIndex = approveAndStake(alice, periodIndex, 10 ether, 10 days, 1 days, 5000, address(0));

        vm.warp(block.timestamp + 10 days + 1 days + 1 seconds);

        vm.startPrank(alice);
        staking.withdraw(stakeIndex);

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.AlreadyWithdrawn.selector, stakeIndex));
        staking.withdraw(stakeIndex);
        vm.stopPrank();
    }

    function test_Staking_RevertWhen_WithdrawNonExistingStake() public {
        deal(address(token), address(staking), 1000 ether);
        uint256 initialAliceBalance = 100 ether;
        deal(address(token), alice, initialAliceBalance);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 10, 5000, true);
        uint8 stakeIndex = approveAndStake(alice, periodIndex, 10 ether, 10 days, 10, 5000, address(0));

        vm.warp(block.timestamp + 10 days + 1 seconds);

        vm.startPrank(alice);
        staking.withdraw(stakeIndex);

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakeNotFound.selector, stakeIndex + 1));
        staking.withdraw(stakeIndex + 1);
        vm.stopPrank();
    }

    function test_Staking_RevertWhen_WithdrawNotUnlockedStake() public {
        deal(address(token), address(staking), 1000 ether);
        uint256 initialAliceBalance = 100 ether;
        deal(address(token), alice, initialAliceBalance);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 10, 5000, true);
        uint8 stakeIndex = approveAndStake(alice, periodIndex, 10 ether, 10 days, 10, 5000, address(0));
        uint64 lockTimestamp = uint64(block.timestamp);

        vm.warp(block.timestamp + 4 days);

        vm.expectRevert(
            abi.encodeWithSelector(
                IStakingV1.RewardsNotAvailableYet.selector, lockTimestamp + 4 days, lockTimestamp + 10 days
            )
        );
        vm.prank(alice);
        staking.withdraw(stakeIndex);
    }

    function test_Staking_RevertWhen_GetClaimableOnNonExistingStake() public {
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.StakeNotFound.selector));
        staking.getClaimable(alice, 1);
    }

    function test_Staking_GetActiveTotalStackedAndRewards() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);
        deal(address(token), bob, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 6 days, 5 days, 5000, true);

        vm.warp(1 days);

        assertEq(staking.activeTotalStaked(), 0);
        assertEq(staking.activeTotalRewards(), 0);

        approveAndStake(alice, periodIndex, 7 ether, 6 days, 5 days, 5000, address(0));
        assertEq(staking.activeTotalStaked(), 7 ether);
        uint256 aliceReward = calculateReward(7 ether, 6 days, 5000);
        assertEq(staking.activeTotalRewards(), aliceReward);

        approveAndStake(bob, periodIndex, 2 ether, 6 days, 5 days, 5000, address(0));
        assertEq(staking.activeTotalStaked(), 9 ether);
        uint256 bobReward = calculateReward(2 ether, 6 days, 5000);
        assertEq(staking.activeTotalRewards(), aliceReward + bobReward);

        vm.warp(8 days);

        uint256 accruedAmountAlice = uint256(7 ether * 1 days) / 5 days;
        uint256 accruedRewardAlice = uint256(aliceReward * 1 days) / 5 days;

        vm.prank(alice);
        staking.withdraw(0);
        assertEq(staking.activeTotalStaked(), 9 ether - accruedAmountAlice);
        assertEq(staking.activeTotalRewards(), aliceReward + bobReward - accruedRewardAlice);

        vm.warp(20 days);

        vm.prank(bob);
        staking.withdraw(0);
        assertEq(staking.activeTotalStaked(), 7 ether - accruedAmountAlice);
        assertEq(staking.activeTotalRewards(), aliceReward - accruedRewardAlice);
    }

    function test_Manage_Pause() public {
        vm.startPrank(pauser);

        assertEq(staking.paused(), false);
        staking.pause();
        assertEq(staking.paused(), true);
        staking.unpause();
        assertEq(staking.paused(), false);

        vm.stopPrank();
    }

    function test_Manage_RevertWhen_UnauthorizedPause() public {
        vm.startPrank(admin);

        vm.expectRevert(
            abi.encodeWithSelector(
                IAccessControl.AccessControlUnauthorizedAccount.selector, admin, staking.PAUSER_ROLE()
            )
        );
        staking.pause();
    }

    function test_Manage_RevertWhen_UnauthorizedUnpause() public {
        vm.startPrank(alice);

        vm.expectRevert(
            abi.encodeWithSelector(
                IAccessControl.AccessControlUnauthorizedAccount.selector, alice, staking.PAUSER_ROLE()
            )
        );
        staking.pause();
    }

    function test_Manage_RevertWhen_StakeWhilePaused() public {
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 10, 5000, true);

        vm.prank(pauser);
        staking.pause();

        vm.expectRevert(abi.encodeWithSelector(Pausable.EnforcedPause.selector));
        stake(alice, periodIndex, 10 ether, 10 days, 10, 5000, address(0));
    }

    function test_Manage_Recover() public {
        deal(address(token), address(staking), 1000 ether);

        uint256 amountToRecover = 50 ether;

        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Recovered(address(token), manager, amountToRecover);
        vm.prank(manager);
        staking.recoverERC20(address(token), amountToRecover);

        assertEq(token.balanceOf(address(staking)), 1000 ether - amountToRecover);
        assertEq(token.balanceOf(manager), amountToRecover);
    }

    function test_Manage_RecoverUnsupportedToken() public {
        deal(address(unsupportedToken), address(staking), 1000 ether);
        deal(address(token), address(staking), 100 ether);
        deal(address(token), alice, 100 ether);

        uint256 amountToRecover = 1000 ether;

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 10, 5000, true);
        approveAndStake(alice, periodIndex, 10 ether, 10 days, 10, 5000, address(0));

        vm.expectEmit(true, true, true, true);
        emit IStakingV1.Recovered(address(unsupportedToken), manager, amountToRecover);
        vm.prank(manager);
        staking.recoverERC20(address(unsupportedToken), amountToRecover);

        assertEq(unsupportedToken.balanceOf(address(staking)), 1000 ether - amountToRecover);
        assertEq(unsupportedToken.balanceOf(manager), amountToRecover);
    }

    function test_Manage_RevertWhen_RecoverExcessiveAmount() public {
        deal(address(token), address(staking), 100 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 10 days, 10, 5000, true);
        approveAndStake(alice, periodIndex, 10 ether, 10 days, 10, 5000, address(0));

        uint256 aliceReward = calculateReward(10 ether, 10 days, 5000);
        uint256 possibleToWithdraw = 100 ether - aliceReward;

        vm.startPrank(manager);
        vm.expectRevert(
            abi.encodeWithSelector(
                IStakingV1.NotEnoughBalanceToRecover.selector, token, possibleToWithdraw + 1, possibleToWithdraw
            )
        );
        staking.recoverERC20(address(token), possibleToWithdraw + 1);

        staking.recoverERC20(address(token), possibleToWithdraw);
        assertEq(token.balanceOf(address(staking)), 100 ether + 10 ether - possibleToWithdraw);
        assertEq(token.balanceOf(manager), possibleToWithdraw);
        vm.stopPrank();
    }

    function test_Manage_RevertWhen_RecoverMoreThanContractHave() public {
        deal(address(token), address(staking), 1000 ether);

        vm.expectRevert(
            abi.encodeWithSelector(IStakingV1.NotEnoughBalanceToRecover.selector, token, 2000 ether, 1000 ether)
        );
        vm.prank(manager);
        staking.recoverERC20(address(token), 2000 ether);
    }

    function test_Manage_RevertWhen_UnauthorizedRecover() public {
        deal(address(token), address(staking), 1000 ether);

        vm.expectRevert(
            abi.encodeWithSelector(
                IAccessControl.AccessControlUnauthorizedAccount.selector, alice, staking.MANAGER_ROLE()
            )
        );
        vm.prank(alice);
        staking.recoverERC20(address(token), 50 ether);
    }

    function test_Migration_SetMigrationPermit() public {
        assertEq(staking.migrationPermits(migrator, alice), false);
        vm.startPrank(alice);

        staking.setMigrationPermit(migrator, true);
        assertEq(staking.migrationPermits(migrator, alice), true);

        staking.setMigrationPermit(migrator, false);
        assertEq(staking.migrationPermits(migrator, alice), false);

        vm.stopPrank();
    }

    function test_Migration_RevertWhen_SetIncorrectMigrator() public {
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.MigratorNotFound.selector, bob));
        vm.prank(alice);
        staking.setMigrationPermit(bob, true);
    }

    function test_Migration_SetMigrationPermit_IdempotentNoOp() public {
        vm.recordLogs();
        vm.prank(alice);
        staking.setMigrationPermit(migrator, false);
        assertEq(vm.getRecordedLogs().length, 0);

        vm.prank(alice);
        staking.setMigrationPermit(migrator, true);

        vm.recordLogs();
        vm.prank(alice);
        staking.setMigrationPermit(migrator, true);
        assertEq(vm.getRecordedLogs().length, 0);
    }

    function test_Migration_RemoveMigrationPermitAfterMigratorRoleRevoke() public {
        assertEq(staking.migrationPermits(migrator, alice), false);

        vm.prank(alice);
        staking.setMigrationPermit(migrator, true);
        assertEq(staking.migrationPermits(migrator, alice), true);

        vm.prank(admin);
        staking.revokeRole(keccak256("MIGRATOR"), migrator);
        assertEq(staking.hasRole(keccak256("MIGRATOR"), migrator), false);

        vm.prank(alice);
        staking.setMigrationPermit(migrator, false);
        assertEq(staking.migrationPermits(migrator, alice), false);
    }

    function test_Migration_SupportIMigratorV1() public view {
        bytes4 erc165InterfaceId = type(IERC165).interfaceId;
        bytes4 fromInterfaceId = type(IMigratorV1).interfaceId;
        bytes4 stakingInterfaceId = type(IStakingV1).interfaceId;
        bytes4 toInterfaceId = type(IMigratorReceiverV2).interfaceId;
        assertEq(staking.supportsInterface(erc165InterfaceId), true);
        assertEq(staking.supportsInterface(fromInterfaceId), true);
        assertEq(staking.supportsInterface(stakingInterfaceId), true);
        assertEq(staking.supportsInterface(toInterfaceId), false);
    }

    function test_Migration_Migrate() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);
        deal(address(token), bob, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);
        approveAndStake(alice, periodIndex, 10 ether, 20, 10, 5000, address(0));
        approveAndStake(bob, periodIndex, 10 ether, 20, 10, 5000, address(0));

        vm.prank(alice);
        staking.setMigrationPermit(migrator, true);
        assertEq(staking.getUserStakes(alice).length, 1);

        uint256 aliceReward = calculateReward(10 ether, 20, 5000);
        vm.expectEmit(true, true, true, true);
        emit IStakingV1.MigratedFrom(migrator, alice, 1, 10 ether, aliceReward);
        vm.prank(migrator);
        IStakingV1.UserStake[] memory migratedStakes = staking.migratePositionsFrom(alice);
        assertEq(migratedStakes.length, 1);
        assertEq(migratedStakes[0].amount, 10 ether);
        assertEq(staking.getUserStakes(alice).length, 0);
        assertEq(staking.getUserStakes(bob).length, 1);
    }

    function test_Migration_MigrateIgnoringWithdrawnStakes() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndexLong = addStakingPeriodByManager(50 ether, 1000, 10, 5000, true);
        uint8 periodIndexShort = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);
        approveAndStake(alice, periodIndexLong, 8 ether, 1000, 10, 5000, address(0));
        approveAndStake(alice, periodIndexShort, 7 ether, 20, 10, 5000, address(0));
        approveAndStake(alice, periodIndexShort, 4 ether, 20, 10, 5000, address(0));

        vm.warp(500); // Enough to finish short stake period

        vm.startPrank(alice);
        staking.withdraw(1);
        staking.setMigrationPermit(migrator, true);
        vm.stopPrank();

        assertEq(staking.getUserStakes(alice).length, 3);
        assertEq(staking.activeTotalStaked(), 12 ether);
        assertEq(
            staking.activeTotalRewards(), calculateReward(8 ether, 1000, 5000) + calculateReward(4 ether, 20, 5000)
        );

        vm.prank(migrator);
        IStakingV1.UserStake[] memory migratedStakes = staking.migratePositionsFrom(alice);
        assertEq(migratedStakes.length, 2);
        assertEq(migratedStakes[0].amount, 8 ether);
        assertEq(migratedStakes[1].amount, 4 ether);

        assertEq(staking.getUserStakes(alice).length, 0);
        assertEq(staking.activeTotalStaked(), 0);
        assertEq(staking.activeTotalRewards(), 0);
    }

    function test_Migration_MigrateMaxStakesGasConsumption() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 20, 10, 5000, true);
        uint8 maxStakesPerUser = staking.MAX_STAKES_PER_USER();
        for (uint256 i = 0; i < maxStakesPerUser; i++) {
            approveAndStake(alice, periodIndex, 0.001 ether + i, 20, 10, 5000, address(0));
        }

        vm.prank(alice);
        staking.setMigrationPermit(migrator, true);

        uint256 gasBefore = gasleft();
        vm.prank(migrator);
        IStakingV1.UserStake[] memory migratedStakes = staking.migratePositionsFrom(alice);
        uint256 gasUsed = gasBefore - gasleft();

        assertEq(migratedStakes.length, maxStakesPerUser);
        assertLe(gasUsed, 12e5); // 1_200_000 Gas
    }

    function test_Migration_MigratePartiallyWithdrawnStake() public {
        deal(address(token), address(staking), 1000 ether);
        deal(address(token), alice, 100 ether);

        vm.warp(1 days);

        uint8 periodIndex = addStakingPeriodByManager(50 ether, 4 days, 3 days, 5000, true);
        approveAndStake(alice, periodIndex, 5 ether, 4 days, 3 days, 5000, address(0));

        vm.warp(7 days);

        vm.startPrank(alice);
        staking.withdraw(0);
        staking.setMigrationPermit(migrator, true);
        vm.stopPrank();

        uint256 aliceReward = calculateReward(5 ether, 4 days, 5000);
        uint256 accruedAmountAlice = uint256(5 ether * 2 days) / 3 days;
        uint256 accruedRewardAlice = uint256(aliceReward * 2 days) / 3 days;

        assertEq(staking.activeTotalStaked(), 5 ether - accruedAmountAlice);
        assertEq(staking.activeTotalRewards(), aliceReward - accruedRewardAlice);

        vm.prank(migrator);
        IStakingV1.UserStake[] memory migratedStakes = staking.migratePositionsFrom(alice);
        assertEq(migratedStakes[0].amount, 5 ether);
        assertEq(migratedStakes[0].claimedAmount, accruedAmountAlice);
        assertEq(migratedStakes[0].reward, aliceReward);
        assertEq(migratedStakes[0].claimedReward, accruedRewardAlice);

        assertEq(staking.activeTotalStaked(), 0);
        assertEq(staking.activeTotalRewards(), 0);
    }

    function test_Migration_RevertWhen_RevokedMigrator() public {
        deal(address(token), address(staking), 1000 ether);

        vm.prank(alice);
        staking.setMigrationPermit(migrator, true);

        vm.prank(admin);
        staking.revokeRole(keccak256("MIGRATOR"), migrator);

        vm.expectRevert(
            abi.encodeWithSelector(
                IAccessControl.AccessControlUnauthorizedAccount.selector, migrator, staking.MIGRATOR_ROLE()
            )
        );
        vm.prank(migrator);
        staking.migratePositionsFrom(migrator);
    }

    function test_Migration_RevertWhen_MigratorNotPermittedByUser() public {
        vm.expectRevert(abi.encodeWithSelector(IStakingV1.MigratorNotPermitted.selector, migrator, alice));
        vm.prank(migrator);
        staking.migratePositionsFrom(alice);
    }

    function test_Migration_RevertWhen_MigratorExplicitlyDeniedByUser() public {
        vm.prank(alice);
        staking.setMigrationPermit(migrator, false);

        vm.expectRevert(abi.encodeWithSelector(IStakingV1.MigratorNotPermitted.selector, migrator, alice));
        vm.prank(migrator);
        staking.migratePositionsFrom(alice);
    }

    // Helpers

    function addStakingPeriodByManager(
        uint256 cap,
        uint64 stakingDurationSeconds,
        uint64 unlockDurationSeconds,
        uint32 aprBps,
        bool isActive
    ) internal returns (uint8 periodIndex) {
        vm.prank(manager);
        periodIndex = staking.addStakingPeriod(cap, stakingDurationSeconds, unlockDurationSeconds, aprBps, isActive);
    }

    function approveAndStake(
        address user,
        uint8 periodIndex,
        uint256 amount,
        uint64 maxStakingDurationSeconds,
        uint64 maxUnlockDurationSeconds,
        uint32 minAprBps,
        address referrer
    ) internal returns (uint8 stakeIndex) {
        vm.startPrank(user);
        token.approve(address(staking), amount);
        stakeIndex = staking.stake(
            periodIndex,
            amount,
            IStakingV1.StakeParams({
                maxStakingDurationSeconds: maxStakingDurationSeconds,
                maxUnlockDurationSeconds: maxUnlockDurationSeconds,
                minAprBps: minAprBps,
                referrer: referrer
            })
        );
        vm.stopPrank();
    }

    function stake(
        address user,
        uint8 periodIndex,
        uint256 amount,
        uint64 maxStakingDurationSeconds,
        uint64 maxUnlockDurationSeconds,
        uint32 minAprBps,
        address referrer
    ) internal returns (uint8 stakeIndex) {
        vm.prank(user);
        stakeIndex = staking.stake(
            periodIndex,
            amount,
            IStakingV1.StakeParams({
                maxStakingDurationSeconds: maxStakingDurationSeconds,
                maxUnlockDurationSeconds: maxUnlockDurationSeconds,
                minAprBps: minAprBps,
                referrer: referrer
            })
        );
    }

    function stakeWithPermit(
        address user,
        uint8 periodIndex,
        uint256 amount,
        uint64 maxStakingDurationSeconds,
        uint64 maxUnlockDurationSeconds,
        uint32 minAprBps,
        address referrer,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) internal returns (uint8 stakeIndex) {
        vm.prank(user);
        stakeIndex = staking.stakeWithPermit(
            periodIndex,
            amount,
            IStakingV1.StakeParams({
                maxStakingDurationSeconds: maxStakingDurationSeconds,
                maxUnlockDurationSeconds: maxUnlockDurationSeconds,
                minAprBps: minAprBps,
                referrer: referrer
            }),
            deadline,
            v,
            r,
            s
        );
    }

    function signCharliePermit(uint256 amount, uint256 deadline) internal view returns (uint8 v, bytes32 r, bytes32 s) {
        return vm.sign(
            charliePrivateKey,
            keccak256(
                abi.encodePacked(
                    "\x19\x01",
                    token.DOMAIN_SEPARATOR(),
                    keccak256(
                        abi.encode(
                            keccak256(
                                "Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)"
                            ),
                            charlie,
                            address(staking),
                            amount,
                            token.nonces(charlie),
                            deadline
                        )
                    )
                )
            )
        );
    }

    function calculateReward(uint256 stakingAmount, uint256 stakingTime, uint256 stakingApyBps)
        internal
        pure
        returns (uint256)
    {
        return (stakingAmount * stakingTime * stakingApyBps) / (365 days * 10000);
    }
}
