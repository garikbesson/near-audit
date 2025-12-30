use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, PanicOnDefault};

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    messages: IterableMap<AccountId, Vec<String>>,
    user_data: IterableMap<AccountId, String>,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            messages: IterableMap::new(b"m".to_vec()),
            user_data: IterableMap::new(b"u".to_vec()),
        }
    }

    // ❌ VULNERABILITY: Storage cost not covered by user
    // Contract pays for storage, attacker can drain contract balance
    #[payable]
    pub fn add_message(&mut self, message: String) {
        let account_id = env::signer_account_id();

        // Missing: assert!(env::attached_deposit() >= storage_cost, "Insufficient deposit");
        // Contract pays storage cost - attacker can spam and drain balance

        let empty_messages = Vec::<String>::new();
        let mut user_messages = self
            .messages
            .get(&account_id)
            .unwrap_or(&empty_messages)
            .to_vec();
        user_messages.push(message);
        self.messages.insert(account_id, user_messages.to_vec());
    }

    // // ❌ VULNERABILITY: User data storage without deposit requirement
    // pub fn store_user_data(&mut self, data: String) {
    //     let user = env::signer_account_id();

    //     // Missing: Check for attached deposit to cover storage
    //     // Attacker can store large amounts of data and drain contract

    //     self.user_data.insert(&user, &data);
    // }

    // // ❌ VULNERABILITY: Collection growth attack
    // pub fn add_item(&mut self, item: String) {
    //     let user = env::signer_account_id();

    //     // Missing: Storage cost check
    //     // Attacker can add thousands of items, draining contract balance

    //     let mut items = self.messages.get(&user).unwrap_or(Vec::new());
    //     items.push(item);
    //     self.messages.insert(&user, &items);
    // }
}
