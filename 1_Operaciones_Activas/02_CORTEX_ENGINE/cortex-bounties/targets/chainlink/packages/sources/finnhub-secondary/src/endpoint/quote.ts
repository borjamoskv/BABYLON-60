// C5-REAL EXERGY CERTIFIED
import { buildQuoteEndpoint } from '@chainlink/finnhub-adapter'
import overrides from '../config/overrides.json'

export const endpoint = buildQuoteEndpoint(overrides.finnhub)
