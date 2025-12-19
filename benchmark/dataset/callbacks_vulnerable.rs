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

    pub fn deposit_and_stake(&mut self) {
        let amount = env::attached_deposit();
        self.pending_user = env::signer_account_id();
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

    // ❌ VULNERABILITY: Callback without #[private] - attacker can call directly
    pub fn callback_after_stake(&mut self, result: Result<(), String>) {
        // Attacker can call this and manipulate state!
        match result {
            Ok(_) => {
                self.balances
                    .insert(&self.pending_user, &self.pending_amount);
            }
            Err(_) => {
                // Attacker can trigger this to rollback legitimate operations
            }
        }
    }

    // ❌ VULNERABILITY: Callback doesn't refund user if external call fails
    #[private]
    pub fn callback_without_refund(&mut self, result: Result<(), String>) {
        match result {
            Err(_) => {
                // VULNERABILITY: User's funds are stuck - should refund!
                // Funds automatically return to contract, but not to user
            }
            Ok(_) => {
                self.balances
                    .insert(&self.pending_user, &self.pending_amount);
            }
        }
    }
}
