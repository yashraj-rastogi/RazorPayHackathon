Extract structured intent from the customer's message.

Allowed intents:
- PAY_NOW
- ASK_TO_DELAY
- STOP
- CONFUSED
- OTHER

Rules:
1. Do not infer intent beyond the text.
2. If a promised date is explicit or clearly expressed, normalize it to YYYY-MM-DD.
3. If no date can be confidently inferred, use null.
4. Do not generate a payment action.
5. Return structured output only.

Return a JSON object with exactly these fields:
{
  "intent": "<one of the allowed intents>",
  "promised_date": "<YYYY-MM-DD or null>",
  "confidence": <float between 0.0 and 1.0>
}
