use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, Gas, NearToken, PanicOnDefault, Promise, PromiseError};

const NO_ARGS: Vec<u8> = vec![];
const XCC_GAS: Gas = Gas::from_tgas(10);

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    balances: IterableMap<AccountId, NearToken>,
    pending_user: AccountId,
    pending_amount: NearToken,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            balances: IterableMap::new(b"b".to_vec()),
            pending_user: "".parse().unwrap(),
            pending_amount: NearToken::ZERO,
        }
    }

    // ❌ VULNERABILITY: Reentrancy attack - state updated before external call
    pub fn deposit_and_stake(&mut self) {
        let amount = env::attached_deposit();
        let account_id = env::signer_account_id();

        // VULNERABILITY: Updates balance BEFORE external call completes
        let balance = self
            .balances
            .get(&account_id)
            .unwrap_or(&NearToken::ZERO)
            .saturating_add(amount);
        self.balances.insert(account_id.clone(), balance);

        // External call - attacker can call withdraw() before callback executes
        self.pending_user = account_id;
        self.pending_amount = amount;

        let _ = Promise::new("validator.near".parse().unwrap())
            .function_call(
                "deposit_and_stake".to_string(),
                NO_ARGS,
                amount,
                Gas::from_tgas(10),
            )
            .then(
                Self::ext(env::current_account_id())
                    .with_static_gas(XCC_GAS)
                    .callback_after_stake(),
            );
    }

    #[private]
    pub fn callback_after_stake(&mut self, #[callback_result] result: Result<(), PromiseError>) {
        match result {
            Err(_) => {
                // Rollback - but attacker may have already withdrawn!
                let balance = self
                    .balances
                    .get(&self.pending_user)
                    .unwrap_or(&NearToken::ZERO)
                    .saturating_sub(self.pending_amount);
                self.balances.insert(self.pending_user.clone(), balance);
            }
            Ok(_) => {}
        }
    }

    // ❌ VULNERABILITY: Can be called between deposit_and_stake and callback
    pub fn withdraw(&mut self, amount: NearToken) {
        let account_id = env::signer_account_id();
        let balance = self.balances.get(&account_id).unwrap_or(&NearToken::ZERO);
        assert!(balance.lt(&amount), "Insufficient balance");

        let new_balance = balance.saturating_sub(amount);
        self.balances.insert(account_id.clone(), new_balance);

        let _ = Promise::new(account_id).transfer(amount);
    }
}
