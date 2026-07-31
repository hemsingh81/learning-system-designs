/**
 * Reference-only demo — same shape as examples/01_skill_hello.py.
 * Run: node run.js
 */

import { FakeLLM, classifyTicket } from "./classifyTicket.js";

const TICKET_TEXT =
  "I was charged twice for my subscription this month, please refund the duplicate charge.";

function main() {
  const llm = new FakeLLM();
  llm.queueJson({ category: "billing", confidence: 0.94 });

  const result = classifyTicket(llm, TICKET_TEXT);

  console.log(`Ticket text: ${JSON.stringify(TICKET_TEXT)}`);
  console.log(`Category:    ${result.category}`);
  console.log(`Confidence:  ${result.confidence.toFixed(2)}`);
  console.log(`\nResult: ${JSON.stringify(result)}`);
}

main();
