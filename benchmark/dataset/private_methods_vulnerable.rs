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

    // ❌ VULNERABILITY PM-1: Method with 'internal' in name but publicly accessible
    pub fn internal_update_balance(&mut self, account_id: &AccountId, amount: u128) {
        // Anyone can call this! Should be pub(crate) fn
        let mut balance = self.balances.get(account_id).unwrap_or(0);
        balance += amount;
        self.balances.insert(account_id, &balance);
    }

    // ❌ VULNERABILITY PM-2: Method with 'helper' in name but publicly accessible
    pub fn calculate_helper(&self, amount: u128) -> u128 {
        // Anyone can call this! Should be pub(crate) fn
        amount * 100 / 10000
    }

    // ❌ VULNERABILITY PM-3: Callback method without #[private]
    pub fn callback_after_staking(&mut self, result: Result<u128, String>) {
        // Attacker can call this directly!
        match result {
            Ok(shares) => {
                self.balances
                    .insert(&self.pending_user, &self.pending_amount);
            }
            Err(_) => {
                // Attacker can trigger this to manipulate state
            }
        }
    }

    // ❌ VULNERABILITY PM-3: Method with 'on_' prefix but unprotected
    pub fn on_transfer_complete(&mut self, success: bool) {
        // Name indicates callback but no protection!
        if success {
            self.balances
                .insert(&self.pending_user, &self.pending_amount);
        }
    }

    // ❌ VULNERABILITY PM-3: Method with 'after_' prefix but unprotected
    pub fn after_deposit(&mut self, result: Result<(), String>) {
        // Name indicates callback but no protection!
        match result {
            Ok(_) => {
                self.balances
                    .insert(&self.pending_user, &self.pending_amount);
            }
            Err(_) => {}
        }
    }

    // ❌ VULNERABILITY PM-5: Manual predecessor check (should use #[private])
    pub fn internal_process(&mut self) {
        assert_eq!(
            env::predecessor_account_id(),
            env::current_account_id(),
            "Only contract can call this method"
        );
        // Should use #[private] instead
    }

    pub fn deposit(&mut self) {
        let amount = env::attached_deposit();
        self.pending_user = env::signer_account_id();
        self.pending_amount = amount;

        // ❌ VULNERABILITY PM-4: Callback called via .then() but not protected
        Promise::new(AccountId::new_unchecked("validator.near".to_string()))
            .function_call("stake".to_string(), b"{}".to_vec(), 0, 0)
            .then(
                env::current_account_id(),
                "callback_after_staking",
                b"{}".to_vec(),
                0,
                0,
            );
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
