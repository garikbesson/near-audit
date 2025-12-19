use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::UnorderedMap;
use near_sdk::{env, near, AccountId};

#[near(contract_state)]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Contract {
    tokens: UnorderedMap<AccountId, Vec<String>>,
}

#[near]
impl Contract {
    pub fn new() -> Self {
        Self {
            tokens: UnorderedMap::new(b"t".to_vec()),
        }
    }

    // ❌ VULNERABILITY: NFT transfer without 1 yoctoNEAR check
    // Website with Function Call key can transfer without user approval
    pub fn transfer_nft(&mut self, token_id: String, receiver_id: AccountId) {
        let owner = self.get_token_owner(&token_id);
        assert_eq!(env::predecessor_account_id(), owner, "Not the owner");

        // Missing: assert!(env::attached_deposit() >= 1, "Must attach 1 yoctoNEAR");

        self.transfer_token(token_id, receiver_id);
    }

    // ❌ VULNERABILITY: Fungible token transfer without 1 yoctoNEAR check
    pub fn transfer_ft(&mut self, amount: u128, receiver_id: AccountId) {
        // Missing: assert!(env::attached_deposit() >= 1, "User verification required");

        let sender = env::predecessor_account_id();
        self.internal_transfer(sender, receiver_id, amount);
    }

    // ❌ VULNERABILITY: Large NEAR transfer without 1 yoctoNEAR check
    pub fn transfer_large_amount(&mut self, receiver_id: AccountId, amount: u128) {
        // Missing: assert!(env::attached_deposit() >= 1, "User verification required");

        let sender = env::predecessor_account_id();
        let balance = self.get_balance(&sender);
        assert!(balance >= amount, "Insufficient balance");

        Promise::new(receiver_id).transfer(amount);
    }

    fn get_token_owner(&self, token_id: &String) -> AccountId {
        // Implementation omitted
        AccountId::new_unchecked("owner.near".to_string())
    }

    fn transfer_token(&mut self, token_id: String, receiver_id: AccountId) {
        // Implementation omitted
    }

    fn internal_transfer(&mut self, sender: AccountId, receiver: AccountId, amount: u128) {
        // Implementation omitted
    }

    fn get_balance(&self, account: &AccountId) -> u128 {
        // Implementation omitted
        0
    }
}
