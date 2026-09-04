# Polymarket API verification — 2026-09-04

This file records version-sensitive official documentation used for implementation.
Values such as fees, limits, and rewards are observations, not architectural constants.

## Public discovery and market metadata

- [Market data overview](https://docs.polymarket.com/market-data/overview): public
  REST market data requires no API key, authentication, or wallet; Gamma exposes
  events and markets; `enableOrderBook` indicates CLOB availability.
- [List markets](https://docs.polymarket.com/api-reference/markets/list-markets):
  `GET https://gamma-api.polymarket.com/markets` exposes condition/question IDs,
  outcome and CLOB token arrays, active/closed/restricted status, tick size, minimum
  size, fee/reward and NegRisk-related metadata where present.
- [Get market by token](https://docs.polymarket.com/api-reference/markets/get-market-by-token):
  `GET https://clob.polymarket.com/markets-by-token/{token_id}` returns condition ID,
  primary Yes token ID, and secondary No token ID.

## Market data

- [Market WebSocket channel](https://docs.polymarket.com/api-reference/wss/market):
  public subscriptions use asset IDs; messages include full `book` snapshots,
  `price_change`, last trade, and tick-size changes. Client ping is documented every
  10 seconds. The documented schema does not promise a conventional monotonic
  sequence number, so Polibot must not invent one.

## Fees and incentives

- [Fees](https://docs.polymarket.com/trading/fees): fees are per-market, may be
  enabled by market metadata, and parameters should be queried dynamically. Any
  displayed category rates can change and are not copied into code constants.
- [Positions and tokens](https://docs.polymarket.com/concepts/positions-tokens):
  Holding Rewards are variable and subject to change. No current percentage is
  encoded in strategy logic.
- [Liquidity rewards](https://docs.polymarket.com/market-makers/liquidity-rewards):
  reward programs and scoring are program-specific and time-sensitive; discovery
  and dated observations are required.

## Trading and non-live adapter semantics

- [Order lifecycle](https://docs.polymarket.com/concepts/order-lifecycle): all orders
  are limits; GTC rests until fill/cancel, GTD expires at its date, FOK must fill in
  full immediately, and FAK accepts an immediate partial fill and kills the rest.
  Post-only is rejected if it would cross and therefore guarantees maker behavior.
- [Trading overview](https://docs.polymarket.com/trading/overview): CLOB V2 orders
  are EIP-712 signed and authenticated trading operations use L2 credentials. Polibot
  implements no real signer or authenticated transport in this milestone.
- [Cancel all](https://docs.polymarket.com/api-reference/trade/cancel-all-orders):
  `DELETE /cancel-all` returns cancelled and not-cancelled results and remains
  available in cancel-only mode.
- [Heartbeat](https://docs.polymarket.com/api-reference/trade/send-heartbeat): missed
  authenticated heartbeats cause all open user orders to be cancelled. Only the
  interface and fake behavior are modeled here; no account call was made.
- [Rate limits](https://docs.polymarket.com/api-reference/rate-limits): endpoint limits
  are externally managed and must inform bounded runtime throttling dynamically;
  current numeric values are not constants in domain code.
- [CLOB V2 migration](https://docs.polymarket.com/v2-migration): production moved to
  V2 on 2026-04-28, legacy V1 signing is unsupported, timestamps contribute to order
  uniqueness, and fee schedules are dynamic. No wire serializer is implemented.

## CTF and settlement semantics

- [Positions and tokens](https://docs.polymarket.com/concepts/positions-tokens):
  splitting collateral creates an equal Yes/No pair, merging consumes equal pairs
  for collateral, and resolved winning tokens redeem for collateral.
- [Gasless transactions](https://docs.polymarket.com/trading/gasless): the relayer can
  carry split/merge/redeem transaction calls and has explicit nonterminal/terminal
  transaction states. Polibot models transaction intents and simulation only.
- [Contracts](https://docs.polymarket.com/resources/contracts): official addresses
  are version-sensitive configuration data. None are embedded in Polibot code.

## Remaining verification

Exact vanilla NegRisk conversion call encoding and augmentation/Other semantics were
not sufficiently specified by the official pages reviewed. The conversion interface
therefore remains generic and all ambiguous structures are `UNSUPPORTED`.
Authenticated user-stream and account endpoints were not exercised because no keys
were requested or used.

## Runtime verification result

On 2026-09-04, an unauthenticated `GET /markets?limit=1&offset=0` smoke test from
the local CPython runtime exhausted the client's three bounded attempts with connect
timeouts. No public payload was received or recorded. Therefore discovery is marked
`TESTED_OFFLINE`, not `TESTED_AGAINST_PUBLIC_API`; recorded official-shape fixtures
and mock transports cover the mapping and failure behavior until connectivity is available.
