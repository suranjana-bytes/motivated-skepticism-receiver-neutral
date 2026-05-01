import csv
import itertools
import random
import sqlite3
import time
from functools import lru_cache
from pathlib import Path

from otree.api import *


doc = """
Receiver-only experiment with instructions, an IQ section, 10 decision rounds,
and final demographics.
"""


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SENDER_DB_PATH = BASE_DIR.parent / "Thesis Experiment" / "db.sqlite3"
RAVEN_PARTICIPANTS_PATH = BASE_DIR / "receiver_experiment" / "raven_participants.csv"
SENDER_DECISIONS_PATH = BASE_DIR / "receiver_experiment" / "sender_decisions.csv"


class C(BaseConstants):
    NAME_IN_URL = "receiver_experiment"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 10
    IQ_TIME_LIMIT_SECONDS = 10 * 60
    TOTAL_EXPERIMENT_SCREENS = 40
    NUMBER_CHOICES = [1, 2, 3]
    STATUS_CHOICES = ["High Status", "Low Status"]
    POINTS_FOR_CORRECT_GUESS = cu(1)
    IQ_OPTION_VALUES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
    EDUCATION_LEVELS = [
        "High School diploma",
        "Bachelors Degree",
        "Master's Degree or Above",
    ]
    GENDER_OPTIONS = [
        "Male",
        "Female",
        "Other/prefer not to say",
    ]
    IQ_ITEMS = [
        dict(question_id="Q2", correct="R1"),
        dict(question_id="Q8", correct="R1"),
        dict(question_id="Q11", correct="R5"),
        dict(question_id="Q12", correct="R6"),
        dict(question_id="Q15", correct="R2"),
        dict(question_id="Q17", correct="R6"),
        dict(question_id="Q18", correct="R7"),
        dict(question_id="Q24", correct="R3"),
        dict(question_id="Q26", correct="R2"),
        dict(question_id="Q30", correct="R5"),
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    sender_id = models.StringField(blank=True)
    sender_number = models.IntegerField()
    sender_status = models.StringField()
    sender_message = models.StringField()
    participant_iq_score = models.IntegerField(blank=True)
    participant_iq_performance = models.FloatField(blank=True)
    previous_participant_1_id = models.StringField(blank=True)
    previous_participant_1_score = models.IntegerField(blank=True)
    previous_participant_1_performance = models.FloatField(blank=True)
    previous_participant_2_id = models.StringField(blank=True)
    previous_participant_2_score = models.IntegerField(blank=True)
    previous_participant_2_performance = models.FloatField(blank=True)
    iq_rank = models.IntegerField(blank=True)
    guess = models.IntegerField(
        choices=C.NUMBER_CHOICES,
        widget=widgets.RadioSelect,
        label="",
    )
    iq_answer_1 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_2 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_3 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_4 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_5 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_6 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_7 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_8 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_9 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    iq_answer_10 = models.StringField(choices=C.IQ_OPTION_VALUES, blank=True)
    age = models.IntegerField(
        choices=list(range(18, 101)),
        blank=True,
        label="1. What is your age?",
    )
    gender = models.StringField(
        choices=C.GENDER_OPTIONS,
        widget=widgets.RadioSelect,
        blank=True,
        label="2. What is your gender?",
    )
    education_level = models.StringField(
        choices=C.EDUCATION_LEVELS,
        widget=widgets.RadioSelect,
        blank=True,
        label="3. What is your highest level of education?",
    )


def creating_session(subsession: Subsession):
    for player in subsession.get_players():
        assign_sender_round_data(player)


def build_sender_message(true_number: int) -> str:
    valid_messages = []
    for subset_size in range(1, len(C.NUMBER_CHOICES) + 1):
        for subset in itertools.combinations(C.NUMBER_CHOICES, subset_size):
            if true_number in subset:
                valid_messages.append(subset)

    message_numbers = random.choice(valid_messages)
    return "{" + ",".join(str(number) for number in message_numbers) + "}"


def sender_message_numbers(sender_message: str):
    inner = sender_message.strip("{}")
    return [int(part.strip()) for part in inner.split(",") if part.strip()]


def receiver_message_display(sender_message: str) -> str:
    numbers = sender_message_numbers(sender_message)
    if len(numbers) == 1:
        number_text = str(numbers[0])
    else:
        number_text = ", ".join(str(number) for number in numbers[:-1])
        number_text = f"{number_text} or {numbers[-1]}"
    return f"It is {number_text}"


@lru_cache(maxsize=1)
def load_raven_participants():
    if not RAVEN_PARTICIPANTS_PATH.exists():
        return []

    participants = []
    with RAVEN_PARTICIPANTS_PATH.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            try:
                answered_items = int(row["answered_items"])
                raven_score = int(row["raven_score"])
            except (KeyError, TypeError, ValueError):
                continue

            if answered_items <= 0:
                continue

            participants.append(
                dict(
                    participant_id=str(row.get("participant_id", "")).strip(),
                    raven_score=raven_score,
                    answered_items=answered_items,
                    raven_performance=raven_score / answered_items,
                )
            )
    return participants


def raven_comparison_pairs():
    participants = load_raven_participants()
    if len(participants) < 2:
        return []

    pairs = list(itertools.combinations(participants, 2))
    random.shuffle(pairs)

    if len(pairs) >= C.NUM_ROUNDS:
        return pairs[: C.NUM_ROUNDS]

    return [
        tuple(random.sample(participants, 2))
        for _ in range(C.NUM_ROUNDS)
    ]


def computed_iq_rank(current_performance: float, previous_pair) -> int:
    group = [
        dict(role="current", performance=current_performance),
        dict(role="previous", performance=previous_pair[0]["raven_performance"]),
        dict(role="previous", performance=previous_pair[1]["raven_performance"]),
    ]
    random.shuffle(group)
    group.sort(key=lambda item: item["performance"], reverse=True)
    for index, item in enumerate(group, start=1):
        if item["role"] == "current":
            return index
    return random.choice(C.NUMBER_CHOICES)


@lru_cache(maxsize=1)
def load_sender_decisions_from_csv():
    if not SENDER_DECISIONS_PATH.exists():
        return {}

    decisions_by_participant = {}
    with SENDER_DECISIONS_PATH.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            try:
                sender_id = str(row["sender_id"]).strip()
                round_number = int(row["round_number"])
                type_number = int(row["type_number"])
                sent_message = str(row["sent_message"]).strip()
                sender_status = str(row["sender_status"]).strip()
            except (KeyError, TypeError, ValueError):
                continue

            if not sender_id or not sender_status or not sent_message:
                continue

            decisions_by_participant.setdefault(sender_id, {})[round_number] = dict(
                sender_id=sender_id,
                sender_status=sender_status,
                sender_number=type_number,
                sender_message=sent_message,
            )
    return decisions_by_participant


@lru_cache(maxsize=1)
def load_sender_decisions_from_db():
    if not DEFAULT_SENDER_DB_PATH.exists():
        return {}

    query = """
        SELECT participant_id, round_number, sender_status, type_number, sent_message
        FROM sender_experiment_player
        WHERE participant_id IS NOT NULL
          AND round_number IS NOT NULL
          AND sender_status IS NOT NULL
          AND type_number IS NOT NULL
          AND sent_message IS NOT NULL
        ORDER BY participant_id, round_number
    """

    try:
        with sqlite3.connect(DEFAULT_SENDER_DB_PATH) as connection:
            rows = connection.execute(query).fetchall()
    except sqlite3.Error:
        return {}

    decisions_by_participant = {}
    for participant_id, round_number, sender_status, type_number, sent_message in rows:
        decisions_by_participant.setdefault(participant_id, {})[round_number] = dict(
            sender_id=str(participant_id),
            sender_status=sender_status,
            sender_number=type_number,
            sender_message=sent_message,
        )
    return decisions_by_participant


def load_sender_decisions():
    csv_decisions = load_sender_decisions_from_csv()
    if csv_decisions:
        return csv_decisions
    return load_sender_decisions_from_db()


def imported_sender_round_for_number(round_number: int, sender_number: int):
    matching_current_round = []
    matching_any_round = []

    for rounds in load_sender_decisions().values():
        for sender_round_number, decision in rounds.items():
            if decision["sender_number"] != sender_number:
                continue
            if sender_number not in sender_message_numbers(decision["sender_message"]):
                continue
            matching_any_round.append(decision)
            if sender_round_number == round_number:
                matching_current_round.append(decision)

    if matching_current_round:
        return random.choice(matching_current_round)
    if matching_any_round:
        return random.choice(matching_any_round)
    return None


def sender_round_data_for_number(round_number: int, sender_number: int):
    imported_round = imported_sender_round_for_number(round_number, sender_number)
    if imported_round:
        return dict(
            sender_id=imported_round.get("sender_id", ""),
            sender_number=sender_number,
            sender_status=imported_round.get("sender_status", "Neutral"),
            sender_message=imported_round["sender_message"],
        )
    return dict(
        sender_id="",
        sender_number=sender_number,
        sender_status="Neutral",
        sender_message=build_sender_message(sender_number),
    )


def assign_sender_round_data(player: Player, sender_number=None):
    if sender_number is None:
        sender_number = random.choice(C.NUMBER_CHOICES)
    else:
        sender_number = int(sender_number)

    sender_data = sender_round_data_for_number(player.round_number, sender_number)
    player.sender_id = sender_data["sender_id"]
    player.sender_number = sender_data["sender_number"]
    player.sender_status = sender_data["sender_status"]
    player.sender_message = sender_data["sender_message"]


def instruction_progress(screen_number: int) -> dict:
    total = 2
    return dict(
        phase_label="",
        screen_counter=f"Screen {screen_number} of {total}",
        progress_percent=(screen_number / C.TOTAL_EXPERIMENT_SCREENS) * 100,
    )


def round_progress(player: Player, screen_number: int) -> dict:
    total = 2
    completed = 17 + ((player.round_number - 1) * total) + screen_number
    return dict(
        phase_label="",
        screen_counter=(
            f"Round {player.round_number} of {C.NUM_ROUNDS} "
            f"- Screen {screen_number} of {total}"
        ),
        progress_percent=(completed / C.TOTAL_EXPERIMENT_SCREENS) * 100,
    )


def iq_progress(screen_number: int) -> dict:
    total = len(C.IQ_ITEMS)
    return dict(
        phase_label="",
        screen_counter=f"Matrix {screen_number} of {total}",
        progress_percent=((3 + screen_number) / C.TOTAL_EXPERIMENT_SCREENS) * 100,
    )


def info_context(**kwargs) -> dict:
    defaults = dict(
        round_chip="",
        bullets=[],
        secondary_bullets=[],
        instruction_lines=[],
        heading_class="",
        status_badge_class="",
        status_badge="",
        message_box="",
        footer="",
    )
    defaults.update(kwargs)
    return defaults


def iq_item(item_number: int) -> dict:
    item = C.IQ_ITEMS[item_number - 1].copy()
    question_id = item["question_id"]
    item["item_number"] = item_number
    item["stem_path"] = f"receiver_experiment/raven/{question_id}/stem.png"
    item["prompt"] = "Select the option that best completes the matrix."
    item["options"] = [
        dict(
            value=option_value,
            label=str(index),
            image_path=f"receiver_experiment/raven/{question_id}/{option_value}.png",
        )
        for index, option_value in enumerate(C.IQ_OPTION_VALUES, start=1)
    ]
    return item


def iq_score(player: Player) -> int:
    round_one = player.in_round(1)
    answers = [
        round_one.iq_answer_1,
        round_one.iq_answer_2,
        round_one.iq_answer_3,
        round_one.iq_answer_4,
        round_one.iq_answer_5,
        round_one.iq_answer_6,
        round_one.iq_answer_7,
        round_one.iq_answer_8,
        round_one.iq_answer_9,
        round_one.iq_answer_10,
    ]
    return sum(
        1 for answer, item in zip(answers, C.IQ_ITEMS) if answer == item["correct"]
    )


def random_iq_rank_schedule() -> list[int]:
    ranks = []
    while len(ranks) < C.NUM_ROUNDS:
        ranks.extend(C.NUMBER_CHOICES)
    ranks = ranks[: C.NUM_ROUNDS]
    random.shuffle(ranks)
    return ranks


def assign_iq_rank_data(player: Player):
    if "iq_rank_schedule" not in player.participant.vars:
        current_score = iq_score(player)
        current_performance = current_score / len(C.IQ_ITEMS)
        comparison_pairs = raven_comparison_pairs()
        random_ranks = random_iq_rank_schedule()
        schedule = []

        for round_number in range(1, C.NUM_ROUNDS + 1):
            round_data = dict(
                participant_iq_score=current_score,
                participant_iq_performance=current_performance,
            )

            if comparison_pairs:
                previous_pair = comparison_pairs[round_number - 1]
                previous_1, previous_2 = previous_pair
                iq_rank = random_ranks[round_number - 1]
                round_data.update(
                    previous_participant_1_id=previous_1["participant_id"],
                    previous_participant_1_score=previous_1["raven_score"],
                    previous_participant_1_performance=previous_1["raven_performance"],
                    previous_participant_2_id=previous_2["participant_id"],
                    previous_participant_2_score=previous_2["raven_score"],
                    previous_participant_2_performance=previous_2["raven_performance"],
                    iq_rank=iq_rank,
                )
            else:
                iq_rank = random_ranks[round_number - 1]
                round_data.update(
                    previous_participant_1_id="",
                    previous_participant_1_score=None,
                    previous_participant_1_performance=None,
                    previous_participant_2_id="",
                    previous_participant_2_score=None,
                    previous_participant_2_performance=None,
                    iq_rank=iq_rank,
                )

            round_data.update(sender_round_data_for_number(round_number, iq_rank))
            schedule.append(round_data)

        player.participant.vars["iq_rank_schedule"] = schedule

    round_data = player.participant.vars["iq_rank_schedule"][player.round_number - 1]
    player.participant_iq_score = round_data["participant_iq_score"]
    player.participant_iq_performance = round_data["participant_iq_performance"]
    player.previous_participant_1_id = round_data["previous_participant_1_id"]
    player.previous_participant_1_score = round_data["previous_participant_1_score"]
    player.previous_participant_1_performance = round_data[
        "previous_participant_1_performance"
    ]
    player.previous_participant_2_id = round_data["previous_participant_2_id"]
    player.previous_participant_2_score = round_data["previous_participant_2_score"]
    player.previous_participant_2_performance = round_data[
        "previous_participant_2_performance"
    ]
    player.iq_rank = round_data["iq_rank"]
    player.sender_id = round_data["sender_id"]
    player.sender_number = round_data["sender_number"]
    player.sender_status = round_data["sender_status"]
    player.sender_message = round_data["sender_message"]


def assign_all_iq_rank_data(player: Player):
    assign_iq_rank_data(player)
    for round_player in player.in_all_rounds():
        if round_player.round_number != player.round_number:
            assign_iq_rank_data(round_player)


class StaticInfoPage(Page):
    template_name = "receiver_experiment/InfoPage.html"


class Welcome(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            eyebrow="",
            heading="Welcome to The Study!",
            paragraphs=[],
            button_label="Next",
            **instruction_progress(1),
        )


class ParticipationInformation(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            eyebrow="",
            heading="Information",
            paragraphs=[
                "Before starting the experiment, please read the following information carefully.",
                (
                    "Your participation in this study is voluntary. You are free "
                    "to stop the study at any time, without providing a reason and "
                    "without any negative consequences."
                ),
                (
                    "Please note that you will not receive any real monetary "
                    "payment for participating in this study. The payments "
                    "mentioned are hypothetical and are used only for the purpose "
                    "of the study. But please act as if they are real."
                ),
                (
                    "All the data collected are anonymous and for research "
                    "purposes only. If you have any question during the "
                    "experiment, please send it to suranjana.ac@gmail.com."
                ),
                "The experiment has 2 parts.",
                "⋄ Part 1: IQ-test,",
                "⋄ Part 2: 10 rounds of a game",
                "Instructions are given along the way. It is in your interest to read them carefully!",
                (
                    "By continuing, you confirm that you have read and understood "
                    "this information and agree to participate in the study."
                ),
            ],
            button_label="Next",
            **instruction_progress(2),
        )


class YourRole(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            eyebrow="",
            heading="Your Role",
            paragraphs=[
                "Today, you are a Receiver.",
                (
                    "Another participant that you will be randomly paired with, "
                    "called the Sender, will observe a number from 1, 2 or 3 and "
                    "send you a message containing one or more numbers."
                ),
                "Your task will be to guess the number that the Sender observed.",
            ],
            button_label="Next",
            **instruction_progress(3),
        )


class IQIntro(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            phase_label="",
            screen_counter="Introduction",
            progress_percent=(3 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
            eyebrow="",
            heading="Part 1",
            paragraphs=[
                (
                    "Part 1 consists of a Raven IQ-test, a test frequently used "
                    "to measure intelligence. It measures the ability to reason "
                    "clearly and grasp complexity. Performance in the test is "
                    "often associated with educational success and high future income."
                ),
                (
                    "The test has 10 questions. For every question, you will see "
                    "a pattern with a missing piece."
                ),
                (
                    "Your task is to complete the pattern by choosing one of the "
                    "pieces that are proposed to you."
                ),
                "You will have 10 minutes to answer all the questions.",
                (
                    "Payoff: you will earn 0.50 cents for each correct answer. "
                    "In this part, you can earn up to 5 euros (15 ∗ 0.50)."
                ),
            ],
            button_label="Start IQ Test",
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars["iq_deadline"] = time.time() + C.IQ_TIME_LIMIT_SECONDS


def iq_seconds_remaining(player: Player) -> int:
    deadline = player.participant.vars.get("iq_deadline")
    if not deadline:
        return C.IQ_TIME_LIMIT_SECONDS
    return max(0, int(deadline - time.time()))


class IQQuestion(Page):
    template_name = "receiver_experiment/IQPage.html"
    form_model = "player"
    item_number = 1

    @classmethod
    def is_displayed(cls, player: Player):
        return player.round_number == 1 and iq_seconds_remaining(player) > 0

    @classmethod
    def get_form_fields(cls, player: Player):
        return [f"iq_answer_{cls.item_number}"]

    @classmethod
    def get_timeout_seconds(cls, player: Player):
        return iq_seconds_remaining(player)

    @classmethod
    def vars_for_template(cls, player: Player):
        return dict(
            form_field_name=f"iq_answer_{cls.item_number}",
            item=iq_item(cls.item_number),
            remaining_seconds=iq_seconds_remaining(player),
            **iq_progress(cls.item_number),
        )


class IQQuestion1(IQQuestion):
    item_number = 1


class IQQuestion2(IQQuestion):
    item_number = 2


class IQQuestion3(IQQuestion):
    item_number = 3


class IQQuestion4(IQQuestion):
    item_number = 4


class IQQuestion5(IQQuestion):
    item_number = 5


class IQQuestion6(IQQuestion):
    item_number = 6


class IQQuestion7(IQQuestion):
    item_number = 7


class IQQuestion8(IQQuestion):
    item_number = 8


class IQQuestion9(IQQuestion):
    item_number = 9


class IQQuestion10(IQQuestion):
    item_number = 10


class IQEnd(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        assign_all_iq_rank_data(player)

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            phase_label="",
            screen_counter="Part 1 Complete",
            progress_percent=(14 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
            eyebrow="",
            heading="Part 1 has now ended",
            paragraphs=["Part 2 will begin."],
            button_label="Next",
        )


class Part2Intro(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            phase_label="",
            screen_counter="Part 2",
            progress_percent=(15 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
            eyebrow="",
            heading="Part 2",
            paragraphs=[],
            instruction_lines=[
                dict(text="Part 2 consists of 10 rounds of a 2-player game.", css_class=""),
                dict(text="Today you are a Reciever!", css_class="emphasis-line"),
                dict(text="You will be randomly matched with a sender, you will never know the identity of the other player and this player can be new in each round.", css_class=""),
            ],
            button_label="Next",
        )


class IQTransition(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            phase_label="",
            screen_counter="Instructions",
            progress_percent=(16 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
            eyebrow="",
            heading="Instructions",
            paragraphs=[],
            bullets=[],
            secondary_bullets=[],
            instruction_lines=[
                dict(text="Description of the game: Each round of the game has 4 steps.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="⋄ Step 1: The same IQ-test that you did earlier was also done by a large number of previous participants. In each round of the game, the computer randomly selects 2 previous participants. Together with these participants, you will form a group of 3 participants. Within this group, the computer program compares the performances in the IQ-test. It will then compute your IQ-rank for the round as follows:", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="⋄ If you have the highest performance in the group of 3, your IQ-rank will be 1.", css_class=""),
                dict(text="⋄ If you have the second highest perfance in the group of 3, your IQ-rank will be 2.", css_class=""),
                dict(text="⋄ If you have the lowest perfance in the group of 3, your IQ-rank will be 3.", css_class=""),
                dict(text="⋄ If you have the same performance as other participants in the group, the computer program randomly decides the ranking between these participants and yourself.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="In each round, your IQ-rank will be 1, 2 or 3. The higher your IQ-rank, the worse you performed in the IQ-test relative to the other participants.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="Note: In each round, the computer randomly selects new previous participants whose performance is compared to yours, so your IQ-rank can change across rounds.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="⋄ Step 2: The Sender is informed of a number, which is 1, 2 or 3. This number corresponds to your IQ-rank, but the Sender does not know that this is the case. For him/her, this number has no particular meaning. You are not informed of this IQ-rank, but your task is to guess it.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="⋄ Step 3: Before you guess your IQ-rank, the Sender gives you information about it. This information will take the form of a set of numbers, with the only constraint that your IQ-rank must be part of the set. Said differently, your IQ-rank is always one of the numbers sent by the Sender. For instance, if your IQ-rank is 2, then the Sender can send you any of the sets of numbers given in the table below:", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="Available sets of numbers", css_class=""),
                dict(text="□{1, 2, 3} ", css_class=""),
                dict(text="□{1, 2} ", css_class=""),
                dict(text="□{2, 3} ", css_class=""),
                dict(text="□{2} ", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="⋄ Step 4: The information given by the Sender will be displayed on your screen, and you will finally make your guess. Your guess can be any number between 1 and 3. Once you made your guess, the round is over and a new round starts.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="In each round, the payoffs are as follows. The Sender knows these payoffs too.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="Sender’s Payoff: The Sender’s payoff corresponds exactly to your guess in this round.", css_class=""),
                dict(text="Sender’s payoff = 4 − (your guess)", css_class="formula-line"),
                dict(text="", css_class="spacer-line"),
                dict(text="Simply put, the Sender earns more when you guess a lower number.", css_class="emphasis-line"),
                dict(text="", css_class="spacer-line"),
                dict(text="Your Payoff: Your payoff depends on how close is your guess to your IQ-rank.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="Your payoff = 3 − | your guess − your IQ-rank |", css_class="formula-line"),
                dict(text="", css_class="spacer-line"),
                dict(text="where | your guess − your IQ-rank | is the distance between your guess and your IQ-rank in the round.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="Simply put, you earn more when your guess is closer to your IQ-rank.", css_class="emphasis-line"),
            ],
            button_label="Next",
        )


class GameSummaryInstructions(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            phase_label="",
            screen_counter="Instructions",
            progress_percent=(17 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
            eyebrow="",
            heading="Instructions",
            paragraphs=[],
            bullets=[],
            secondary_bullets=[],
            instruction_lines=[
                dict(text="Each round of the game goes as follows:", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="1. Your IQ-rank is computed.", css_class=""),
                dict(text="2. The Sender is informed about a number that corresponds to your IQ-rank. For him/her, this number has no meaning.", css_class=""),
                dict(text="3. The Sender gives you information about this number.", css_class=""),
                dict(text="4. You receive this information and guess your IQ-rank.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="You earn more when your guess is closer to your IQ-rank. The Sender earns more when you guess a lower number.", css_class=""),
                dict(text="", css_class="spacer-line"),
                dict(text="No feedback: In the experiment, you will never receive more information about your IQ-ranks than the information given by the Senders.", css_class=""),
            ],
            button_label="Start Experiment",
        )


class RoundStart(StaticInfoPage):
    @staticmethod
    def vars_for_template(player: Player):
        assign_iq_rank_data(player)
        return info_context(
            eyebrow="",
            heading="A new round is starting.",
            paragraphs=[
                (
                    "In this round, you will be randomly paired with another Sender."
                ),
                "Your task will be to guess the number that the Sender observed.",
            ],
            round_chip=f"Round {player.round_number} of {C.NUM_ROUNDS}",
            button_label="Next",
            **round_progress(player, 1),
        )


class ReceiverDecision(Page):
    form_model = "player"
    form_fields = ["guess"]

    @staticmethod
    def vars_for_template(player: Player):
        assign_iq_rank_data(player)
        available_numbers = sender_message_numbers(player.sender_message)
        return dict(
            round_label=f"Round {player.round_number} / {C.NUM_ROUNDS}",
            sender_status=player.sender_status,
            sender_message=receiver_message_display(player.sender_message),
            available_numbers=available_numbers,
            available_numbers_text=", ".join(str(number) for number in available_numbers),
            **round_progress(player, 2),
        )

    @staticmethod
    def error_message(player: Player, values):
        available_numbers = sender_message_numbers(player.sender_message)
        if values["guess"] not in available_numbers:
            allowed = ", ".join(str(number) for number in available_numbers)
            return f"Please enter one of the numbers sent by the Sender: {allowed}."

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guess = player.field_maybe_none("guess")
        player.payoff = (
            C.POINTS_FOR_CORRECT_GUESS
            if guess == player.sender_number
            else cu(0)
        )


class DemographicsIntro(StaticInfoPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return info_context(
            phase_label="",
            screen_counter="Introduction",
            progress_percent=(38 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
            eyebrow="",
            heading="Part 2 has now ended",
            paragraphs=[
                "Before finishing the study, please complete a short demographic questionnaire.",
                "Your responses will remain confidential and will only be used for research purposes.",
            ],
            button_label="Start Questionnaire",
        )


class DemographicsQuestionnaire(Page):
    template_name = "receiver_experiment/Demographics.html"
    form_model = "player"
    form_fields = ["age", "gender", "education_level"]

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            phase_label="",
            screen_counter="Questionnaire",
            progress_percent=(39 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
        )


class StudyComplete(Page):
    template_name = "receiver_experiment/FinalRound.html"

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        total_correct = sum(
            1
            for past_player in player.in_all_rounds()
            if past_player.field_maybe_none("guess") == past_player.sender_number
        )
        return dict(
            total_correct=total_correct,
            total_points=player.participant.payoff,
            iq_total=iq_score(player),
            phase_label="",
            screen_counter="Completed",
            progress_percent=(40 / C.TOTAL_EXPERIMENT_SCREENS) * 100,
        )


page_sequence = [
    Welcome,
    ParticipationInformation,
    IQIntro,
    IQQuestion1,
    IQQuestion2,
    IQQuestion3,
    IQQuestion4,
    IQQuestion5,
    IQQuestion6,
    IQQuestion7,
    IQQuestion8,
    IQQuestion9,
    IQQuestion10,
    IQEnd,
    Part2Intro,
    IQTransition,
    GameSummaryInstructions,
    RoundStart,
    ReceiverDecision,
    DemographicsIntro,
    DemographicsQuestionnaire,
    StudyComplete,
]
