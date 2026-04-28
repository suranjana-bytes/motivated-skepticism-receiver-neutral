from . import *
from otree.api import Bot, Submission


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield Welcome
            yield ParticipationInformation
            yield YourRole
            yield IQIntro
            yield IQQuestion1, dict(iq_answer_1="R2")
            yield IQQuestion2, dict(iq_answer_2="R1")
            yield IQQuestion3, dict(iq_answer_3="R3")
            yield IQQuestion4, dict(iq_answer_4="R3")
            yield IQQuestion5, dict(iq_answer_5="R2")
            yield IQQuestion6, dict(iq_answer_6="R6")
            yield IQQuestion7, dict(iq_answer_7="R5")
            yield IQQuestion8, dict(iq_answer_8="R8")
            yield IQQuestion9, dict(iq_answer_9="R4")
            yield IQQuestion10, dict(iq_answer_10="R1")
            yield IQTransition

        yield RoundStart
        yield SenderInformation
        available_numbers = sender_message_numbers(self.player.sender_message)
        yield ReceiverDecision, dict(guess=available_numbers[0])

        if self.round_number == C.NUM_ROUNDS:
            yield DemographicsIntro
            yield DemographicsQuestionnaire, dict(
                age=25,
                gender="Female",
                education_level="Bachelors Degree",
            )
            yield Submission(StudyComplete, check_html=False)
