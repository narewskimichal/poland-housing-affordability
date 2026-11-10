[Overview](../README.md) · [Python](../python/README.md) · [SQL](../sql/README.md) · [Power BI](../powerbi/README.md) · **Copilot Studio**

# Copilot Studio – housing market Q&A agent

A simple chat agent built in Microsoft Copilot Studio. It answers questions about the housing market in the 15 largest Polish cities using only the results of this project, so someone can ask "where are flats cheapest?" instead of looking through the dashboard.

**Main result:** across 15 test questions, all answers had the correct figure from the project or the correct out-of-scope reply. Questions about other cities, today's rates or investment advice were all declined.

## How it works

![Agent overview](img/01_agent_overview.png)

- **Knowledge:** one file, [`knowledge_base.md`](knowledge_base.md). It holds the key numbers from the SQL and Power BI parts (prices, rents, wages, mortgage vs rent, price drivers, price cuts, monthly trends), together with definitions and limitations.
- **Instructions:** answer only from that file, give each number with its unit and period, keep answers short, mention that these are asking prices, and give no investment advice. If a question is outside the project, reply with one fixed sentence. The full setup is in [`agent_instructions.md`](agent_instructions.md).
- **Settings:** web search and access to Microsoft 365 data are switched off, so the agent cannot pull in anything beyond the project data.

![Knowledge source](img/02_knowledge.png)

## Example answers

**Where are flats most and least expensive?** The agent lists the top and bottom five cities and adds the 2.7× gap between Warsaw and Radom. The left panel shows the passages it retrieved from the knowledge file.

![Prices answer](img/03_answer_prices.png)

**How many m² does an average salary buy?** 1.19 m² in Katowice vs 0.60 m² in Warsaw, with the wages used.

![Affordability answer](img/04_answer_affordability.png)

**Mortgage payment vs rent in Wrocław:** 3,958 zł vs 2,900 zł a month, plus the loan assumptions behind it.

![Buy vs rent answer](img/05_answer_buy_vs_rent.png)

**Out of scope:** Gliwice is not one of the 15 cities, and investment advice is not given.

![Out of scope](img/07_out_of_scope.png)

![No investment advice](img/08_no_investment_advice.png)

## Testing

The agent was tested in the Copilot Studio test panel with 15 questions: 12 inside the project and 3 outside it. The questions, expected answers and results are in [`test_questions.md`](test_questions.md).

All 15 answers had the right number or the right refusal. One small issue: an English question got its answer in Polish ([screenshot](img/06_answer_english.png)). The instruction only said "answer in the language of the question", and a stricter rule would most likely fix it.

## Files

| File | What it is |
|---|---|
| [`knowledge_base.md`](knowledge_base.md) | the only knowledge source of the agent |
| [`agent_instructions.md`](agent_instructions.md) | name, description, instructions, settings and conversation starters |
| [`test_questions.md`](test_questions.md) | 15 test questions with expected answers and results |
| `img/` | screenshots |

## Limitations

- The agent only knows what is in the knowledge file. It does not query the database or the Power BI model, so it cannot answer questions the file does not cover.
- The data ends in June 2024, so the agent says nothing about the current market.
- Language models can still phrase things loosely, so the numbers should be checked against the report before they are used.
- The agent was built and tested in a university Microsoft 365 environment and was not published; the screenshots come from the test panel.

