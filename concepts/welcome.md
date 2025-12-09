# NEAR Protocol Smart Contract Security Guide

## Overview

This guide provides comprehensive information on how to keep your NEAR Protocol smart contracts and decentralized applications (dApps) secure. Security is critical in blockchain development, and understanding these concepts will help you build robust, attack-resistant applications.

**Key Topics Covered**: smart contract security, NEAR Protocol security, dApp security, vulnerability prevention, attack mitigation, security best practices, blockchain security

## 🐞 Bug Bounty Program

NEAR Protocol maintains an active bug bounty program hosted on Hackenproof. If you discover security vulnerabilities in the NEAR protocol, core contracts, or web infrastructure, please report them through the official bug bounty program rather than exploiting them.

**Program Link**: https://hackenproof.com/company/near/programs

**Why Report**: Responsible disclosure helps protect the entire NEAR ecosystem. Security researchers and developers who identify and report vulnerabilities help make NEAR more secure for everyone.

**Related Terms**: bug bounty, responsible disclosure, security audit, vulnerability reporting, white hat hacking

## ✅ Security Checklist

Before deploying your smart contract to mainnet, always run through the comprehensive security checklist. This checklist covers critical areas including:

- Method access control and visibility
- Environment variable usage (predecessor, signer)
- Storage cost management
- State consistency
- Cross-contract call handling
- Error handling and rollbacks

**See the full checklist**: [Security Checklist](./checklist.md)

**Related Terms**: security audit, deployment checklist, contract verification, security review, pre-deployment testing

## 🛡️ Core Security Concepts

Understanding these fundamental security concepts is essential for building secure NEAR smart contracts:

### 1. Callback Security
**Topic**: [Keeping Callbacks Safe](./callbacks.md)
- Securing callback methods from unauthorized access
- Handling user funds in cross-contract calls
- Preventing reentrancy through proper callback design
- Managing state consistency between calls and callbacks

**Related Terms**: callbacks, cross-contract calls, async execution, state management, access control

### 2. Frontrunning Attacks
**Topic**: [Understanding Frontrunning](./frontrunning.md)
- How validators can see transactions before execution
- Strategies to prevent frontrunning attacks
- Protecting reward mechanisms and game mechanics

**Related Terms**: frontrunning, MEV (Maximal Extractable Value), transaction ordering, validator manipulation

### 3. Sybil Attacks
**Topic**: [Understanding Sybil Attacks](./sybil.md)
- Multiple account creation for malicious purposes
- Impact on voting and governance systems
- Protection strategies for DAOs and community decisions

**Related Terms**: sybil attack, account creation, voting manipulation, DAO security, governance attacks

### 4. Reentrancy Attacks
**Topic**: [Understanding Reentrancy Attacks](./reentrancy.md)
- How attackers can re-enter contracts during execution
- State consistency between method calls and callbacks
- Prevention patterns and best practices

**Related Terms**: reentrancy, state consistency, race conditions, attack vectors, security vulnerabilities

### 5. Access Key Verification
**Topic**: [Ensuring the Owner is Calling](./one_yocto.md)
- Verifying that transactions come from the actual user
- Function Call keys vs Full Access keys
- Using 1 yoctoNEAR to force wallet confirmation

**Related Terms**: access keys, function call keys, full access keys, user verification, transaction authorization

### 6. Random Number Generation
**Topic**: [Generating Random Numbers](./random.md)
- Understanding NEAR's deterministic random seed
- Validator manipulation risks
- Gaming the input attacks
- Refusing to mine blocks attacks
- Best practices for randomness in smart contracts

**Related Terms**: random seed, deterministic randomness, validator manipulation, gaming attacks, block mining

### 7. Storage Cost Attacks
**Topic**: [Protecting from Storage Drain Attacks](./storage.md)
- How storage costs work in NEAR
- Small deposit attacks that drain contract funds
- Requiring users to cover their own storage costs
- Releasing locked storage balance

**Related Terms**: storage costs, storage rent, balance management, storage attacks, cost attacks

## 🎞️ External Learning Resources

**Smart Contract Security Video Series**

An excellent video series on Smart Contract Security by security expert Timurguvenkaya provides in-depth explanations of common vulnerabilities and attack vectors. These videos complement the written documentation and provide visual explanations of complex security concepts.

**YouTube Channel**: Search for "Smart Contract Security" by @timurguvenkaya

**Related Terms**: security education, video tutorials, security training, blockchain security courses

## Best Practices Summary

1. **Always review the security checklist** before mainnet deployment
2. **Understand each security concept** before implementing related features
3. **Test thoroughly** with edge cases and attack scenarios
4. **Get code reviews** from security-conscious developers
5. **Report vulnerabilities** through the official bug bounty program
6. **Stay updated** on new attack vectors and security best practices

## Common Questions This Guide Answers

- What security concepts should I understand for NEAR contracts?
- How do I secure callbacks in cross-contract calls?
- What is a reentrancy attack and how do I prevent it?
- How can I verify that a user is actually making a transaction?
- How do storage costs work and how can they be exploited?
- What is frontrunning and how does it affect my contract?
- How do I generate secure random numbers in NEAR?
- What is a sybil attack and how does it affect DAOs?