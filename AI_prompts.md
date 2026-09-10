# AI Prompts Log

Record of prompts typed in my own words as homework problems are worked.

## Setup

- I need to get my homework organized before i start it. please create a prompts/ folder and an output/ folder. We are going to add one script per problem as we go. I also need an AI_prompts.md file that records all the prompts I actually type as i enter them. Do not do this problem until i ask you in my own words what I want done. Ask me to type the task in my own words first please. Prepare sections for each of problems 2 - 9. Each section needs the problem number and title and at least one prompt I typed in my own words. i'll do the rest unless or until i say otherwise
- you don't have to look up problems yet we're going to do them, i just want to set up that they're coming

## Problem 2: Extract purchase receipts

### Prompts

- create a script called read_receipts.py that calls an LLM using the prompt in prompts/receipts_extract.md. I will upload a zip file here, let me know if that's not what you need. then extract one row per purchase receipt PDF in the document pack and save a JSON array of those rows to output/receipts.json. Each row should contain the vendor (store or seller name), date (transaction date), description (what was purchased), amount_usd (total for this receipt in dollars), category (expense labor, for example cogs_parts, tools_equipment, or shipping); source_file (filename of hte PDF the row came from). Put missing fields in "Fields_not_found" - don't invent anything! here's the command format python read_receipts.py --docs-dir PATH --out-dir output. --docs-dir is the unzipped pack. emails\email_fleet_wellness.txt emails\email_owner_voice_memo.txt emails\email_wedding_ebikes.txt emails\email_yale_cycling_club.txt manifest.json pdfs\bank_statement_jan2026.pdf pdfs\credit_card_jan2026.pdf pdfs\ebay_repair_stand.pdf pdfs\iou_mike_smith.pdf pdfs\lease_jan2026.pdf pdfs\quote_hartford_mutual_fleet.pdf pdfs\receipt_amazon_headphones.pdf pdfs\receipt_courier.pdf pdfs\receipt_home_depot.pdf pdfs\receipt_nhbp_parts.pdf pdfs\receipt_park_tool.pdf

## Problem 3: Jan bank statement transactions

### Prompts

- ok good now we need to handle the Jan. bank statement. each line needs a business or personal category and an accounting category so i can reconcile it with reciepts and credit card charges. Please create a script called read_bank.py that calls an LLM using the prompt in bank_extract.md from bankstatement_jan2026.pdf, then save a json array of those rows to output/bank_transactions.json. (Let me know if you can't find anything i'm referencing.) Each bank line must include: date (posting or transaction date), a description (text shown on the statement), amount_usd (the dollar amount, a positive number only), classification (busienss or personal), direction / credit (money in) or debit (money out), accounting_label (what kind of work this is; rent, utilities, cogs_parts) and omit null or otherwise. please run it with the command format python read_bank.py --docs-dir PATH --out-dir output. If i'm giving you too much information please let me know, i'm really new at this. ALSO, this goes under problem 3 and make sure you're tracking my prompts please

## Problem 4: Credit card transactions

### Prompts

- ok here comes #4. we need to extract some credit card transactions to fully reconcile them in the next step to come, because the credit card statmenet overlaps with receipts but uses categories that are too broad for us. please create a script read_card.py that calls an LLM using the prompt in prompts/card_extract.md to pull each charge from credit_card_jan2026.pdf, and save a json array of those rows to output/credit_card_transactions.json. each charge must include date (the charge date), merchant (the name on the statement), amount_usd (charge amount in dollars), classification (business or personal), expense_category (business expense label for shop charges; use null for personal rows) Script shoudl run with: python read_card.py --docs-dir PATH --out-dir output

## Problem 5: [Title TBD]

### Prompts

- _(add the prompt you type in your own words here before we start this problem)_

## Problem 6: [Title TBD]

### Prompts

- _(add the prompt you type in your own words here before we start this problem)_

## Problem 7: [Title TBD]

### Prompts

- _(add the prompt you type in your own words here before we start this problem)_

## Problem 8: [Title TBD]

### Prompts

- _(add the prompt you type in your own words here before we start this problem)_

## Problem 9: [Title TBD]

### Prompts

- _(add the prompt you type in your own words here before we start this problem)_
