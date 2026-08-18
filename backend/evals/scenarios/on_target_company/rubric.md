The user asked about the company with ticker {{expected.ticker}}.

User's question:
{{input}}

Agent's response:
{{output}}

Every part of the response should serve the user's question about
{{expected.ticker}}. Content about other companies or the broader market is
acceptable only when it directly supports the answer — for example, a peer
comparison or market context that helps explain {{expected.ticker}}'s situation.

Score Y if all content in the response serves the answer to the user's question
about {{expected.ticker}}.

Score N if any content about another company stands on its own rather than
supporting the answer — unprompted news, analysis, or commentary about a company
the user did not ask about, regardless of length.
