use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, PanicOnDefault};

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    votes: IterableMap<AccountId, bool>,
    yes_votes: u64,
    no_votes: u64,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            votes: IterableMap::new(b"v".to_vec()),
            yes_votes: 0,
            no_votes: 0,
        }
    }

    // ❌ VULNERABILITY: One-account-one-vote - attacker can create multiple accounts
    pub fn vote(&mut self, vote: bool) {
        let voter = env::signer_account_id();

        // No checks for multiple accounts from same person
        // Attacker can create 100 accounts and vote 100 times

        if !self.votes.contains_key(&voter) {
            self.votes.insert(voter, vote);

            if vote {
                self.yes_votes += 1;
            } else {
                self.no_votes += 1;
            }
        }
    }

    // // ❌ VULNERABILITY: Airdrop without Sybil protection
    // pub fn claim_airdrop(&mut self) {
    //     let account = env::signer_account_id();

    //     // No identity verification - attacker can claim multiple times
    //     // with different accounts
    //     if !self.has_claimed(&account) {
    //         self.mark_as_claimed(&account);
    //         // Distribute tokens
    //     }
    // }

    // // ❌ VULNERABILITY: Reputation system without Sybil protection
    // pub fn rate_user(&mut self, target: AccountId, rating: u8) {
    //     let rater = env::signer_account_id();

    //     // Attacker can create multiple accounts to boost/attack reputation
    //     self.add_rating(&target, &rater, rating);
    // }

    // fn has_claimed(&self, account: &AccountId) -> bool {
    //     // Implementation omitted
    //     false
    // }

    // fn mark_as_claimed(&mut self, account: &AccountId) {
    //     // Implementation omitted
    // }

    // fn add_rating(&mut self, target: &AccountId, rater: &AccountId, rating: u8) {
    //     // Implementation omitted
    // }
}
