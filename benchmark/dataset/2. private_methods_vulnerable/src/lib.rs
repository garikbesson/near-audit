use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, NearToken, PanicOnDefault};

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    balances: IterableMap<AccountId, NearToken>,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            balances: IterableMap::new(b"b".to_vec()),
        }
    }

    #[payable]
    pub fn deposit(&mut self) {
        let amount = env::attached_deposit();
        let account_id = env::signer_account_id();
        self.internal_update_balance(account_id, amount);
    }

    // ❌ VULNERABILITY PM-1: Method with 'internal' in name but publicly accessible
    pub fn internal_update_balance(&mut self, account_id: AccountId, amount: NearToken) {
        // Anyone can call this! Should be pub(crate) fn
        let balance = self.balances.get(&account_id).unwrap_or(&NearToken::ZERO);
        let new_balance = balance.saturating_add(amount);
        self.balances.insert(account_id, new_balance);
    }

    // // ❌ VULNERABILITY PM-2: Method with 'helper' in name but publicly accessible
    // pub fn calculate_helper(&self, amount: u128) -> u128 {
    //     // Anyone can call this! Should be pub(crate) fn
    //     amount * 100 / 10000
    // }

    // // ❌ VULNERABILITY PM-3: Method with 'on_' prefix but unprotected
    // pub fn on_transfer_complete(&mut self, success: bool) {
    //     // Name indicates callback but no protection!
    //     if success {
    //         self.balances
    //             .insert(&self.pending_user, &self.pending_amount);
    //     }
    // }

    // // ❌ VULNERABILITY PM-3: Method with 'after_' prefix but unprotected
    // pub fn after_deposit(&mut self, result: Result<(), String>) {
    //     // Name indicates callback but no protection!
    //     match result {
    //         Ok(_) => {
    //             self.balances
    //                 .insert(&self.pending_user, &self.pending_amount);
    //         }
    //         Err(_) => {}
    //     }
    // }

    // ❌ VULNERABILITY PM-5: Manual predecessor check (should use #[private])
    pub fn internal_process(&mut self) {
        assert_eq!(
            env::predecessor_account_id(),
            env::current_account_id(),
            "Only contract can call this method"
        );
        // Should use #[private] instead
    }
}

// ✅ SAFE: This impl block is NOT decorated, so methods are NOT public
impl Contract {
    pub fn internal_helper(&self) -> u128 {
        // DO NOT FLAG - not in #[near] impl block
        // This is safe even though it's pub fn
        100
    }

    pub fn helper_calculate(&self, amount: u128) -> u128 {
        // DO NOT FLAG - not in #[near] impl block
        amount * 2
    }
}
