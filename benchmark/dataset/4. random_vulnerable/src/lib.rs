use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, NearToken, PanicOnDefault};

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    bets: IterableMap<AccountId, String>,
    rewards: IterableMap<AccountId, NearToken>,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            bets: IterableMap::new(b"b".to_vec()),
            rewards: IterableMap::new(b"r".to_vec()),
        }
    }

    // ❌ VULNERABILITY: Gaming the input - validator can predict and win
    // User provides input and random seed is generated in same block
    pub fn guess_number(&mut self, guess: u8) {
        let account_id = env::signer_account_id();

        // Store user's guess
        self.bets.insert(account_id.clone(), guess.to_string());

        // Generate random number in SAME block - validator knows it!
        let random_seed = env::random_seed();
        let random_number = (random_seed[0] % 100) as u8;

        // Validator can see user's guess and create winning transaction
        if guess == random_number {
            let reward = NearToken::from_near(1);
            let previous_user_reward = self.rewards.get(&account_id).unwrap_or(&NearToken::ZERO);
            let user_reward = previous_user_reward.saturating_add(reward);
            self.rewards.insert(account_id, user_reward);
        }
    }

    // // ❌ VULNERABILITY: Refusing to mine - validator skips losing blocks
    // // Two-stage process but validator can still manipulate
    // pub fn bet_heads_or_tails(&mut self, choice: String) {
    //     let user = env::signer_account_id();
    //     self.bets.insert(&user, &choice);
    //     // Resolve happens in separate method, but validator can skip it if they'd lose
    // }

    // pub fn resolve_bet(&mut self) {
    //     let user = env::signer_account_id();
    //     let choice = self.bets.get(&user).unwrap();

    //     // Validator knows random seed and can skip this if they'd lose
    //     let random_seed = env::random_seed();
    //     let outcome = if random_seed[0] % 2 == 0 {
    //         "heads"
    //     } else {
    //         "tails"
    //     };

    //     if choice == outcome {
    //         let reward = 2000;
    //         let mut user_reward = self.rewards.get(&user).unwrap_or(0);
    //         user_reward += reward;
    //         self.rewards.insert(&user, &user_reward);
    //     }
    // }
}
