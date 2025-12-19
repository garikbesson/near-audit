use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::UnorderedMap;
use near_sdk::{env, near, AccountId, Promise};

#[near(contract_state)]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Contract {
    balances: UnorderedMap<AccountId, u128>,
    pending_user: AccountId,
    pending_amount: u128,
}

#[near]
impl Contract {
    pub fn new() -> Self {
        Self {
            balances: UnorderedMap::new(b"b".to_vec()),
            pending_user: AccountId::new_unchecked("".to_string()),
            pending_amount: 0,
        }
    }

    // ❌ VULNERABILITY: Reentrancy attack - state updated before external call
    pub fn deposit_and_stake(&mut self) {
        let amount = env::attached_deposit();
        let user = env::signer_account_id();

        // VULNERABILITY: Updates balance BEFORE external call completes
        let mut balance = self.balances.get(&user).unwrap_or(0);
        balance += amount;
        self.balances.insert(&user, &balance);

        // External call - attacker can call withdraw() before callback executes
        self.pending_user = user.clone();
        self.pending_amount = amount;

        Promise::new(AccountId::new_unchecked("validator.near".to_string()))
            .function_call("stake".to_string(), b"{}".to_vec(), 0, 0)
            .then(
                env::current_account_id(),
                "callback_after_stake",
                b"{}".to_vec(),
                0,
                0,
            );
    }

    #[private]
    pub fn callback_after_stake(&mut self, result: Result<(), String>) {
        match result {
            Err(_) => {
                // Rollback - but attacker may have already withdrawn!
                let mut balance = self.balances.get(&self.pending_user).unwrap_or(0);
                balance -= self.pending_amount;
                self.balances.insert(&self.pending_user, &balance);
            }
            Ok(_) => {}
        }
    }

    // ❌ VULNERABILITY: Can be called between deposit_and_stake and callback
    pub fn withdraw(&mut self, amount: u128) {
        let user = env::signer_account_id();
        let balance = self.balances.get(&user).unwrap_or(0);
        assert!(balance >= amount, "Insufficient balance");

        let new_balance = balance - amount;
        self.balances.insert(&user, &new_balance);

        Promise::new(user).transfer(amount);
    }
}
