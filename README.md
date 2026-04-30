# Receiver Experiment

This workspace includes an `oTree` app called `receiver_experiment` for a receiver-only study with an instruction sequence, a timed Raven IQ section, a 10-round receiver task, demographics, and a final thank-you screen.

## What it includes

- consent and study information screens
- 10 timed Raven-style IQ items
- Part 2 game instructions
- 10 decision rounds
- sender messages generated/imported to always include the true number
- receiver IQ-rank guesses
- final demographics questionnaire
- final thank-you screen

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
