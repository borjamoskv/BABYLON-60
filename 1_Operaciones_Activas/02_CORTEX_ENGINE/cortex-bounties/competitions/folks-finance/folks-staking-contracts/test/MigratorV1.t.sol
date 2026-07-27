// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {ERC20Permit, ERC20} from "openzeppelin-contracts/contracts/token/ERC20/extensions/ERC20Permit.sol";
import {IERC20Errors} from "openzeppelin-contracts/contracts/interfaces/draft-IERC6093.sol";
import {ERC165} from "openzeppelin-contracts/contracts/utils/introspection/ERC165.sol";
import {Test} from "forge-std/Test.sol";
import {MigratorV1} from "../src/test/MigratorV1.sol";
import {StakingV1Mock} from "../src/test/mock/StakingV1Mock.sol";
import {StakingV2Mock} from "../src/test/mock/StakingV2Mock.sol";
import {IStakingV1} from "../src/interfaces/IStakingV1.sol";
import {IMigratorV1} from "../src/interfaces/IMigratorV1.sol";
import {IMigratorReceiverV2} from "../src/interfaces/IMigratorReceiverV2.sol";

contract TokenA is ERC20Permit {
    constructor() ERC20Permit("TestTokenA") ERC20("TestTokenA", "ATKN") {}
}

contract TokenB is ERC20Permit {
    constructor() ERC20Permit("TestTokenB") ERC20("TestTokenB", "BTKN") {}
}

contract RandomContractWithERC165 is ERC165 {}

contract MigratorV1Test is Test {
    StakingV1Mock public stakingV1Mock;
    StakingV2Mock public stakingV2Mock;
    StakingV2Mock public stakingV2MockTokenB;
    MigratorV1 public migrator;
    RandomContractWithERC165 public randomContractWithERC165;

    address public alice = address(11);

    TokenA public tokenA;
    TokenB public tokenB;

    function setUp() public {
        tokenA = new TokenA();
        tokenB = new TokenB();
        stakingV1Mock = new StakingV1Mock(tokenA);
        stakingV2Mock = new StakingV2Mock(tokenA);
        stakingV2MockTokenB = new StakingV2Mock(tokenB);
        migrator = new MigratorV1(stakingV1Mock, stakingV2Mock);

        deal(address(tokenA), address(stakingV1Mock), 1000 ether);
        deal(address(tokenA), address(stakingV2Mock), 1000 ether);
        deal(address(tokenB), address(stakingV2MockTokenB), 1000 ether);
    }

    function test_SetUp() public view {
        assertEq(address(migrator.FROM()), address(stakingV1Mock));
        assertEq(address(migrator.TO()), address(stakingV2Mock));
    }

    function test_Migration_Migrate() public {
        IStakingV1.UserStake[] memory aliceStakes = new IStakingV1.UserStake[](2);
        aliceStakes[0] = IStakingV1.UserStake(1 ether, 0.2 ether, 0, 0, 5000, 10, 10004, 30);
        aliceStakes[1] = IStakingV1.UserStake(6 ether, 0.1 ether, 0, 0, 3000, 7, 10006, 30);
        stakingV1Mock.setUserStakes(alice, aliceStakes);

        migrator.migrate(alice);
        assertEq(tokenA.balanceOf(address(stakingV1Mock)), 1000 ether - 7.3 ether);
        assertEq(tokenA.balanceOf(address(stakingV2Mock)), 1000 ether + 7.3 ether);
        assertEq(tokenA.balanceOf(address(migrator)), 0);
    }

    function test_Migration_RevertWhen_UserStakesEmpty() public {
        vm.expectRevert(abi.encodeWithSelector(MigratorV1.PositionsNotFound.selector, alice));
        migrator.migrate(alice);
    }

    function test_Migration_RevertWhen_RecipientTransferringMoreFundsThanExpected() public {
        IStakingV1.UserStake[] memory aliceStakes = new IStakingV1.UserStake[](1);
        aliceStakes[0] = IStakingV1.UserStake(1 ether, 0.2 ether, 0, 0, 5000, 10, 10004, 30);
        stakingV1Mock.setUserStakes(alice, aliceStakes);
        stakingV2Mock.setMockAmountToTransfer(4 ether);

        vm.expectRevert(
            abi.encodeWithSelector(
                IERC20Errors.ERC20InsufficientAllowance.selector, address(stakingV2Mock), 1.2 ether, 4 ether
            )
        );
        migrator.migrate(alice);
    }

    function test_Migration_RevertWhen_RecipientTransferringLessFundsThanExpected() public {
        IStakingV1.UserStake[] memory aliceStakes = new IStakingV1.UserStake[](1);
        aliceStakes[0] = IStakingV1.UserStake(1 ether, 0.2 ether, 0, 0, 5000, 10, 10004, 30);
        stakingV1Mock.setUserStakes(alice, aliceStakes);
        stakingV2Mock.setMockAmountToTransfer(0.5 ether);

        vm.expectRevert(abi.encodeWithSelector(MigratorV1.InconsistentBalance.selector, 0, 1.2 ether - 0.5 ether));
        migrator.migrate(alice);
    }

    function test_Migration_RevertWhen_SenderTransferringMoreFundsThanExpected() public {
        IStakingV1.UserStake[] memory aliceStakes = new IStakingV1.UserStake[](1);
        aliceStakes[0] = IStakingV1.UserStake(1 ether, 0.2 ether, 0, 0, 5000, 10, 10004, 30);
        stakingV1Mock.setUserStakes(alice, aliceStakes);
        stakingV1Mock.setMockAmountToTransfer(5 ether);

        vm.expectRevert(abi.encodeWithSelector(MigratorV1.InconsistentBalance.selector, 0 ether, 5 ether - 1.2 ether));
        migrator.migrate(alice);
    }

    function test_Migration_RevertWhen_SenderTransferringLessFundsThanExpected() public {
        IStakingV1.UserStake[] memory aliceStakes = new IStakingV1.UserStake[](1);
        aliceStakes[0] = IStakingV1.UserStake(1 ether, 0.2 ether, 0, 0, 5000, 10, 10004, 30);
        stakingV1Mock.setUserStakes(alice, aliceStakes);
        stakingV1Mock.setMockAmountToTransfer(0.4 ether);

        vm.expectRevert(
            abi.encodeWithSelector(
                IERC20Errors.ERC20InsufficientAllowance.selector, address(stakingV2Mock), 0.4 ether, 1.2 ether
            )
        );
        migrator.migrate(alice);
    }

    function test_Migration_RevertWhen_SenderAndReceiverUseDifferentTokens() public {
        MigratorV1 migratorWithDifferentTokens = new MigratorV1(stakingV1Mock, stakingV2MockTokenB);

        vm.expectRevert(abi.encodeWithSelector(MigratorV1.DifferentStakingTokens.selector, tokenA, tokenB));
        migratorWithDifferentTokens.migrate(alice);
    }

    function test_Migration_RevertWhenFromNotSupportIERC165() public {
        bytes4 fromInterfaceId = type(IMigratorV1).interfaceId;
        vm.expectRevert(
            abi.encodeWithSelector(MigratorV1.InterfaceNotSupported.selector, address(tokenA), fromInterfaceId)
        );
        new MigratorV1(IMigratorV1(address(tokenA)), stakingV2MockTokenB);
    }

    function test_Migration_RevertWhenFromNotSupportIMigratorV1Interface() public {
        bytes4 fromInterfaceId = type(IMigratorV1).interfaceId;
        vm.expectRevert(
            abi.encodeWithSelector(
                MigratorV1.InterfaceNotSupported.selector, address(randomContractWithERC165), fromInterfaceId
            )
        );
        new MigratorV1(IMigratorV1(address(randomContractWithERC165)), stakingV2MockTokenB);
    }

    function test_Migration_RevertWhenToNotSupportIERC165() public {
        bytes4 toInterfaceId = type(IMigratorReceiverV2).interfaceId;
        vm.expectRevert(
            abi.encodeWithSelector(MigratorV1.InterfaceNotSupported.selector, address(tokenA), toInterfaceId)
        );
        new MigratorV1(stakingV1Mock, IMigratorReceiverV2(address(tokenA)));
    }

    function test_Migration_RevertWhenToNotSupportIMigratorV1Interface() public {
        bytes4 toInterfaceId = type(IMigratorReceiverV2).interfaceId;
        vm.expectRevert(
            abi.encodeWithSelector(
                MigratorV1.InterfaceNotSupported.selector, address(randomContractWithERC165), toInterfaceId
            )
        );
        new MigratorV1(stakingV1Mock, IMigratorReceiverV2(address(randomContractWithERC165)));
    }
}
