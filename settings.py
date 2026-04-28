from os import environ


SESSION_CONFIGS = [
    dict(
        name="receiver_experiment",
        display_name="Receiver Experiment",
        app_sequence=["receiver_experiment"],
        num_demo_participants=1,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc="Receiver-only experiment where participants infer a sender's number.",
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = "en"
REAL_WORLD_CURRENCY_CODE = "USD"
USE_POINTS = True

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = environ.get("OTREE_ADMIN_PASSWORD", "admin")

DEMO_PAGE_INTRO_HTML = """
<h3>Receiver Experiment</h3>
<p>
    This oTree app runs a 10-round receiver task with instruction screens,
    sender status information, a sender message, and a receiver choice.
</p>
"""

SECRET_KEY = "receiver-experiment-secret-key"

INSTALLED_APPS = ["otree"]
