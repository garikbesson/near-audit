use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::{env, near_bindgen, AccountId, Promise, PromiseResult};

#[near_bindgen]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Contract {
    pub owner: AccountId,
    pub balances: std::collections::HashMap<AccountId, u128>,
}

impl Default for Contract {
    fn default() -> Self {
        Self {
            owner: env::predecessor_account_id(),
            balances: std::collections::HashMap::new(),
        }
    }
}

#[near_bindgen]
impl Contract {
    pub fn deposit(&mut self) {
        let amount = env::attached_deposit();
        let account = env::predecessor_account_id();

        // VULNERABILITY: No storage cost check
        // VULNERABILITY: No user verification (missing 1 yoctoNEAR check)
        let current_balance = self.balances.get(&account).unwrap_or(&0);
        self.balances.insert(account, current_balance + amount);
    }

    pub fn withdraw(&mut self, amount: u128) {
        let account = env::predecessor_account_id();
        let balance = self.balances.get(&account).unwrap_or(&0);

        // VULNERABILITY: Potential reentrancy - state updated before external call
        if *balance >= amount {
            self.balances.insert(account.clone(), balance - amount);

            // External call before state is fully committed
            Promise::new(account).transfer(amount);
        }
    }

    pub fn transfer_to_contract(&mut self, receiver: AccountId, amount: u128) {
        let sender = env::predecessor_account_id();

        // VULNERABILITY: No access control check
        // VULNERABILITY: No callback handling for cross-contract calls
        let sender_balance = self.balances.get(&sender).unwrap_or(&0);

        if *sender_balance >= amount {
            self.balances.insert(sender, sender_balance - amount);
            self.balances.insert(
                receiver.clone(),
                self.balances.get(&receiver).unwrap_or(&0) + amount,
            );

            // Cross-contract call without proper callback handling
            Promise::new(receiver).function_call(
                "receive".to_string(),
                b"{}".to_vec(),
                0,
                env::prepaid_gas() / 2,
            );
        }
    }

    pub fn get_balance(&self, account: AccountId) -> u128 {
        *self.balances.get(&account).unwrap_or(&0)
    }
}
