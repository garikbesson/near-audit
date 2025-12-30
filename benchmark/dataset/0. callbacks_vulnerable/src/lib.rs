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
    #[private] // Private method - only callable by the contract's account
    pub fn new() -> Self {
        Self {
            balances: IterableMap::new(b"b".to_vec()),
            pending_user: "".parse().unwrap(),
            pending_amount: NearToken::ZERO,
        }
    }

    pub fn deposit_and_stake(&mut self) {
        let amount = env::attached_deposit();
        self.pending_user = env::signer_account_id();
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

    // ❌ VULNERABILITY: Callback without #[private] - attacker can call directly
    pub fn callback_after_stake(&mut self, #[callback_result] result: Result<(), PromiseError>) {
        // Attacker can call this and manipulate state!
        match result {
            Ok(_) => {
                self.balances
                    .insert(self.pending_user.clone(), self.pending_amount);
            }
            Err(_) => {
                // Attacker can trigger this to rollback legitimate operations
            }
        }
    }
}
