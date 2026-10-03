content = r"""#Problem 1: Vibe coder prompts

Prompt:
Keep the prompts I use for each problem in `AI_prompts.md` and add the follow up prompts too if I need any.


#Problem 2: Analyze the database

Prompt:
Can you check `data/campus_customs.db` and see what tables and fields are there?

At least check `catalogue`, `inventory` and `users`.

Also update `output/harness.md` with the tables, their fields and a short line on why each field matters for the shop or chatbot.


#Problem 3: Build the Campus Customs website

Prompt:
Can you build the Campus Customs website in React + Vite + TypeScript?

Add Home, Products, About Us, Log in and Create account in the navbar.

For Home and About Us use Campus Customs style wording but write it in your own words.

On Products page show the products from the database with image, name, price and short description.

When I click a product it should open its own page with bigger image, full description, price and sizes/stock if there is any.

Also add a chat box on bottom right.

You can make a small FastAPI backend in `backend/main.py` to serve the products and images.

2nd Prompt:
so its done?

3rd Prompt:
ok, fix them i guess


#Problem 4: Create account and login

Prompt:
Can you add create account and login?

Create account should have first name, last name, email and password. You can add confirm password too.

Login should be email and password.

Save new users in the `users` table and don't save passwords in plain text.

Use this test account too:

Email: `test@campuscustoms.yale.edu`
Password: `password`

Also create a new account and make sure that one can login too.

Update `output/harness.md` with how login works and how the passwords are stored.

2nd Prompt:
yeah, go ahead with 3


#Problem 5: PydanticAI agent backend

Prompt:
Can you build the chatbot backend with PydanticAI and FastAPI and connect it to the frontend chat box?

Keep these files:

`backend/main.py`
`backend/agent.py`
`backend/tools.py`
`backend/models.py`
`backend/prompts/prompt.md`

Use `prompt.md` for the system prompt, `agent.py` for the agent setup, `tools.py` for tools and `models.py` for the Pydantic models.

Add a chat route in `main.py` so the frontend can send a message and get the agent reply back.

Also add the Campus Customs tone and basic safety rules in the prompt.

Update `output/harness.md` with how the frontend talks to FastAPI and how the agent is loaded.

Run it from the backend folder using:

`uvicorn main:app --reload --port 8000`

2nd Prompt:
whats happening here?


#Problem 6: Tools: product info and stock

Prompt:
Can you add tools so the chatbot can get the real product info from `campus_customs.db`?

It should be able to check product description, price, stock and stock by size when someone asks.

Make sure it reads from the database and doesn't make up prices or quantities.

If something is out of stock then say it clearly.

Update `prompts/prompt.md` so the agent knows when to use the tools.

Update `models.py` too if needed.

Also update `output/harness.md` with the tools and the fields you used for the results.


#Problem 7: Chat search that updates the page

Prompt:
Can you make the chatbot search products and show the matching products on the page?

Like if I ask:

`what hoodies do you have?`

it should search the catalogue and show the matching products as cards with image, name, price and short info.

It should update the page without reloading it.

If I click one of those products it should still open the same product detail page from Problem 3.

Also update `prompts/prompt.md` and `output/harness.md` with how the search results get from the chatbot to the frontend.


#Problem 8: Customer memory

Prompt:
Can you add memory for logged in users?

Save their chat history in the database and load it again when they come back.

The chatbot should also know basic user info like name and email.

Also pass the current page/product context to it.

For example if I'm on a product page and ask:

`do you have this in pink?`

it should know which product I mean.

Guests can still use chat but their history doesn't need to be saved.

Update `output/harness.md` with how the history is stored, what user fields are passed and how page context is passed.


#Problem 9: Usability improvements

Prompt:
Can you add 2 frontend usability improvements and 2 chatbot/backend usability improvements?

Frontend ones should make the site easier to use.

Backend/chatbot ones can improve the responses, accuracy, safety or speed.

Create `output/usability.md` and for each one write what you added and why it helps the shopper or business.

Make sure the changes are actually added in the app.


#Problem 10: Style the website

Prompt:
Can you improve the design so the site looks more like a real Campus Customs store?

Improve the fonts, colors, spacing, layout, product cards and chat UI. Add some motion too if it makes sense.

Create `output/design.md` and keep the explanation short. Just write what you changed and why it makes the site better for customers.


#Problem 11: Site testing

Prompt:
Can you test the site and create `output/app_check.html`?

I need screenshots for these:

1. Chatbot checking the real stock or price from the database
2. Product cards showing after asking something like what hoodies do you have
3. One of the usability features from Problem 9

For each one add a heading, screenshot and a short line or two on what it proves.

Save the screenshots in `output/app_check_images/` and use relative paths in `app_check.html`.


#Problem 12: Audit trail, safety and harness

Prompt:
Can you add an audit trail for the chatbot in `output/audit_trail.json`?

It should append new records and not wipe the old ones.

For each agent action save the time, tool name, short args/result and stop reason.

Also add some safety rules in `prompts/prompt.md`.

Finish `output/harness.md` too and include the model fields in `models.py`, tools and what they do, safety rules, loop/result limits, models being used and how to run the frontend and backend.


#Problem 13: Push to GitHub

Prompt:
Can you prepare the project for GitHub?

Put it in a folder named `hw4` and push it to a public GitHub repo.

Don't upload `campus_customs.db`, the product images from the data pack, `.env` or any API keys/secrets.

Use `.gitignore` and add `.env.example`.

Keep the data folder local only.

Also update `README.md` with how to run the frontend and backend after putting the data pack in the right place.

In the end give me the GitHub repo URL.
"""

path = "/mnt/data/AI_prompts_HW4_fixed.md"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(path)
