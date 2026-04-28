# Receiver Experiment

This workspace now includes an `oTree` app called `receiver_experiment` for a study with instructions, an IQ section, a 10-round receiver task, and a demographics questionnaire.

## What it includes

- 7 instruction screens
- 10 Raven-style IQ items
- 10 decision rounds
- sender status shown each round
- sender message generated to always include the sender's true number
- receiver choice and confirmation screen
- final demographics questionnaire
- final thank-you screen with IQ and decision summaries

## Run it

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the local server:

```bash
otree devserver
```

4. Open the local URL shown in the terminal, then launch the `receiver_experiment` session from the oTree demo page.

## Default admin login

- Username: `admin`
- Password: `admin`

Set `OTREE_ADMIN_PASSWORD` in your shell if you want a different password.
