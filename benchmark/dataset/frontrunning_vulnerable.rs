use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::UnorderedMap;
use near_sdk::{env, near, AccountId};

#[near(contract_state)]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Contract {
    solved_puzzles: UnorderedMap<String, AccountId>,
    rewards: UnorderedMap<AccountId, u128>,
}

#[near]
impl Contract {
    pub fn new() -> Self {
        Self {
            solved_puzzles: UnorderedMap::new(b"s".to_vec()),
            rewards: UnorderedMap::new(b"r".to_vec()),
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
                self.solved_puzzles.insert(&puzzle_id, &solver);

                let reward = 10000;
                let mut solver_reward = self.rewards.get(&solver).unwrap_or(0);
                solver_reward += reward;
                self.rewards.insert(&solver, &solver_reward);
            }
        }
    }

    // ❌ VULNERABILITY: Auction without commit-reveal - validator can see bids
    pub fn place_bid(&mut self, item_id: String, bid_amount: u128) {
        // Validator can see all bids in transaction pool
        // Can place higher bid before user's transaction executes
        let bidder = env::signer_account_id();
        let current_bid = self.get_current_bid(&item_id);

        if bid_amount > current_bid {
            self.set_bid(&item_id, &bidder, bid_amount);
        }
    }

    fn get_puzzle_answer(&self, puzzle_id: &String) -> String {
        // Implementation omitted
        "answer".to_string()
    }

    fn get_current_bid(&self, item_id: &String) -> u128 {
        // Implementation omitted
        0
    }

    fn set_bid(&mut self, item_id: &String, bidder: &AccountId, amount: u128) {
        // Implementation omitted
    }
}
