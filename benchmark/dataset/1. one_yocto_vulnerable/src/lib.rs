use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, NearToken, PanicOnDefault, Promise};

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    tokens: IterableMap<AccountId, Vec<String>>,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            tokens: IterableMap::new(b"t".to_vec()),
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
    pub fn transfer_ft(&mut self, amount: NearToken, receiver_id: AccountId) {
        // Missing: assert!(env::attached_deposit() >= 1, "User verification required");

        let sender = env::predecessor_account_id();
        self.internal_transfer(sender, receiver_id, amount);
    }

    // ❌ VULNERABILITY: Large NEAR transfer without 1 yoctoNEAR check
    pub fn transfer_large_amount(&mut self, receiver_id: AccountId, amount: NearToken) {
        // Missing: assert!(env::attached_deposit() >= 1, "User verification required");

        let sender = env::predecessor_account_id();
        let balance = self.get_balance(&sender);
        assert!(balance >= amount, "Insufficient balance");

        let _ = Promise::new(receiver_id).transfer(amount);
    }

    fn get_token_owner(&self, token_id: &String) -> AccountId {
        // Implementation omitted
        "owner.near".parse().unwrap()
    }

    fn transfer_token(&mut self, token_id: String, receiver_id: AccountId) {
        // Implementation omitted
    }

    fn internal_transfer(&mut self, sender: AccountId, receiver: AccountId, amount: NearToken) {
        // Implementation omitted
    }

    fn get_balance(&self, account: &AccountId) -> NearToken {
        // Implementation omitted
        NearToken::from_near(0)
    }
}
