use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::UnorderedMap;
use near_sdk::{env, near, AccountId};

#[near(contract_state)]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Contract {
    messages: UnorderedMap<AccountId, Vec<String>>,
    user_data: UnorderedMap<AccountId, String>,
}

#[near]
impl Contract {
    pub fn new() -> Self {
        Self {
            messages: UnorderedMap::new(b"m".to_vec()),
            user_data: UnorderedMap::new(b"u".to_vec()),
        }
    }

    // ❌ VULNERABILITY: Storage cost not covered by user
    // Contract pays for storage, attacker can drain contract balance
    pub fn add_message(&mut self, message: String) {
        let user = env::signer_account_id();

        // Missing: assert!(env::attached_deposit() >= storage_cost, "Insufficient deposit");
        // Contract pays storage cost - attacker can spam and drain balance

        let mut user_messages = self.messages.get(&user).unwrap_or(Vec::new());
        user_messages.push(message);
        self.messages.insert(&user, &user_messages);
    }

    // ❌ VULNERABILITY: User data storage without deposit requirement
    pub fn store_user_data(&mut self, data: String) {
        let user = env::signer_account_id();

        // Missing: Check for attached deposit to cover storage
        // Attacker can store large amounts of data and drain contract

        self.user_data.insert(&user, &data);
    }

    // ❌ VULNERABILITY: Collection growth attack
    pub fn add_item(&mut self, item: String) {
        let user = env::signer_account_id();

        // Missing: Storage cost check
        // Attacker can add thousands of items, draining contract balance

        let mut items = self.messages.get(&user).unwrap_or(Vec::new());
        items.push(item);
        self.messages.insert(&user, &items);
    }
}
