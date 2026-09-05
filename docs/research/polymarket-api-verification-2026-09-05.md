# Polymarket public API verification — 2026-09-05

This is the implementation record for the continuous PAPER worker. Protocol values
remain dynamic observations; none of the example values are strategy constants.

## Discovery and market identity

- [List markets](https://docs.polymarket.com/api-reference/markets/list-markets)
  documents `GET /markets`, offset pagination, active/closed filters, and activity
  fields including liquidity and 24-hour volume. The worker requests active, open
  markets ordered deterministically by 24-hour volume and applies stricter validation.
- [Get market by token](https://docs.polymarket.com/api-reference/markets/get-market-by-token)
  returns the condition ID and authoritative primary Yes/secondary No token IDs. The
  worker does not infer this mapping from array order or titles.
- [Get CLOB market info](https://docs.polymarket.com/api-reference/markets/get-clob-market-info)
  returns tokens, minimum order size, tick size, base fees, and the fee curve. The
  worker cross-checks tick/minimum values and records a dated fee model per market.
  Missing, invalid, or contradictory values exclude the market.

## Order books and streaming

- [Get order book](https://docs.polymarket.com/api-reference/market-data/get-order-book)
  returns an authoritative token snapshot with condition/token IDs, timestamp, hash,
  levels, minimum order size, tick size, NegRisk flag, and last trade price.
- [Market channel](https://docs.polymarket.com/api-reference/wss/market) documents the
  public asset-ID subscription, dynamic subscription operations, client `PING` every
  10 seconds and server `PONG`, full `book`, `price_change`, `last_trade_price`,
  `tick_size_change`, and opt-in `best_bid_ask` messages. It does not document a
  monotonic sequence number. Polibot therefore relies on timestamps, identity, hashes
  where supplied, invalidation, staleness, and authoritative snapshot recovery.

## Fees and limits

- [Fees](https://docs.polymarket.com/trading/fees) states that fees are per-market and
  determined at match time, and directs clients to CLOB market info. The taker formula
  is applied only using the retrieved market rate and recorded provenance.
- [Rate limits](https://docs.polymarket.com/api-reference/rate-limits) and the
  [changelog](https://docs.polymarket.com/changelog) describe service-managed endpoint
  throttles. The worker uses a bounded market universe, five-minute refresh, timeouts,
  and bounded exponential reconnect rather than treating published maxima as targets.

## NegRisk boundary

The public schemas expose NegRisk and “Other” indicators, but the reviewed documentation
does not establish enough invariants to prove every augmented/Other terminal state for
automatic continuous selection. The offline scanner remains available, but the deployed
worker keeps NegRisk disabled until a separately tested adapter can establish the full
machine-readable payoff set. Titles are never evidence.

## Verification result

Official pages were reviewed on 2026-09-05. A local unauthenticated endpoint smoke
attempt timed out before receiving a Gamma payload, so this workstation is not evidence
of live ingestion. The opt-in `public_api` test remains outside normal CI. Deployment
verification must use increasing counters and database rows from the PAPER host.

No wallet, API credential, order endpoint, or chain transaction was used.
