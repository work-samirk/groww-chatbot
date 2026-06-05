# Sample Chatbot Q&A Logs

The following are verified sample conversations demonstrating the chatbot's RAG responses, compliance checks, intent routing, and citation links.

---

### Q1: Platform Feature Query (Interepted by Heuristics)
* **User**: `How to start a SIP on Groww?`
* **Assistant**:
  > To start a SIP on Groww:
  > 1. Log in to your Groww account.
  > 2. Search for the Groww Mutual Fund scheme you want to invest in.
  > 3. Click on 'Start SIP' and enter your monthly investment amount and date.
  > 4. Complete the one-time KYC and bank mandate setups to automate payments.
  > 
  > **Source**: [https://groww.in/mutual-funds](https://groww.in/mutual-funds) | **Last Updated**: 2026-06-04

---

### Q2: Compliance Refusal on Investment Suggestions
* **User**: `Should I buy Groww Nifty 50 Index Fund?`
* **Assistant**:
  > I can only provide factual, objective details about mutual fund schemes. For investment advice, please consult a registered financial advisor. You can read more about mutual fund investments on AMFI or the SEBI Investor Education Portal.
  > 
  > **Source**: [https://www.mutualfundssahihai.com](https://www.mutualfundssahihai.com)

---

### Q3: Scheme Portfolio / Fund Manager Query (RAG Path)
* **User**: `Who is the fund manager of Groww Nifty 50 Index Fund?`
* **Assistant**:
  > The fund manager of the Groww Nifty 50 Index Fund Direct Growth is **Aakash Ashokkumar Chauhan**.
  > 
  > **Source**: [https://groww.in/mutual-funds/groww-nifty-50-index-fund-direct-growth](https://groww.in/mutual-funds/groww-nifty-50-index-fund-direct-growth) | **Last Updated**: 2026-06-05 04:39:01

---

### Q4: Scheme Specific Details / Minimum Investment (RAG Path)
* **User**: `What is the minimum SIP amount for Groww Gold ETF FOF?`
* **Assistant**:
  > The minimum SIP investment amount for Groww Gold ETF FOF Direct Growth is **₹500**.
  > 
  > **Source**: [https://groww.in/mutual-funds/groww-gold-etf-fof-direct-growth](https://groww.in/mutual-funds/groww-gold-etf-fof-direct-growth) | **Last Updated**: 2026-06-05 04:39:01

---

### Q5: Out of Scope Fund Clarification
* **User**: `What is the return of Groww Focused Fund?`
* **Assistant**:
  > The Groww Focused Fund is not currently active in the Groww mutual fund portfolio, or is not supported. Please select or query about one of the active funds like:
  > - Groww Nifty 50 Index Fund
  > - Groww Aggressive Hybrid Fund
  > - Groww Large Cap Fund
  > - Groww Value Fund
  > - Groww ELSS Tax Saver Fund
  > - Groww Small Cap Fund

---

### Q6: Multi-turn Follow-up Context Resolution
* **User**: `What is the exit load of Groww Liquid Fund?`
* **Assistant**:
  > The exit load for Groww Liquid Fund Direct Growth depends on the redemption period after investment:
  > - Day 1: 0.0070%
  > - Day 2: 0.0065%
  > - Day 3: 0.0060%
  > - Day 4: 0.0055%
  > - Day 5: 0.0050%
  > - Day 6: 0.0045%
  > - Day 7 onwards: Nil
  > 
  > **Source**: [https://groww.in/mutual-funds/groww-liquid-fund-direct-growth](https://groww.in/mutual-funds/groww-liquid-fund-direct-growth) | **Last Updated**: 2026-06-05 04:39:01
* **User**: `and what is its minimum SIP?`
* **Assistant**:
  > The minimum SIP investment for the Groww Liquid Fund Direct Growth is **₹500**.
  > 
  > **Source**: [https://groww.in/mutual-funds/groww-liquid-fund-direct-growth](https://groww.in/mutual-funds/groww-liquid-fund-direct-growth) | **Last Updated**: 2026-06-05 04:39:01
