use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, NearToken, PanicOnDefault};

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    solved_puzzles: IterableMap<String, AccountId>,
    rewards: IterableMap<AccountId, NearToken>,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            solved_puzzles: IterableMap::new(b"s".to_vec()),
            rewards: IterableMap::new(b"r".to_vec()),
        }
    }

    // ❌ VULNERABILITY: First-come-first-served - validator can frontrun
    // Validator sees user's solution in transaction pool and submits it first
    pub fn solve_puzzle(&mut self, puzzle_id: String, solution: String) {
        // Validator can see this transaction in pool and extract solution
        let correct_answer = self.get_puzzle_answer(&puzzle_id);

        if solution == correct_answer {
            // First solver gets reward - validator can frontrun!
            if !self.solved_puzzles.contains_key(&puzzle_id) {
                let solver = env::signer_account_id();
                self.solved_puzzles.insert(puzzle_id, solver.clone());

                let reward = NearToken::from_near(1);
                let previous_solver_reward = self.rewards.get(&solver).unwrap_or(&NearToken::ZERO);
                let solver_reward = previous_solver_reward.saturating_add(reward);
                self.rewards.insert(solver, solver_reward);
            }
        }
    }

    fn get_puzzle_answer(&self, _puzzle_id: &String) -> String {
        // Implementation omitted
        "answer".to_string()
    }

    // // ❌ VULNERABILITY: Auction without commit-reveal - validator can see bids
    // pub fn place_bid(&mut self, item_id: String, bid_amount: u128) {
    //     // Validator can see all bids in transaction pool
    //     // Can place higher bid before user's transaction executes
    //     let bidder = env::signer_account_id();
    //     let current_bid = self.get_current_bid(&item_id);

    //     if bid_amount > current_bid {
    //         self.set_bid(&item_id, &bidder, bid_amount);
    //     }
    // }

    // fn get_current_bid(&self, item_id: &String) -> u128 {
    //     // Implementation omitted
    //     0
    // }

    // fn set_bid(&mut self, item_id: &String, bidder: &AccountId, amount: u128) {
    //     // Implementation omitted
    // }
}
