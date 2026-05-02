from . import *
from otree.api import Bot, Submission


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield Welcome
            yield ParticipationInformation
            yield IQIntro
            yield IQQuestion1, dict(iq_answer_1="R1")
            yield IQQuestion2, dict(iq_answer_2="R1")
            yield IQQuestion3, dict(iq_answer_3="R5")
            yield IQQuestion4, dict(iq_answer_4="R6")
            yield IQQuestion5, dict(iq_answer_5="R2")
            yield IQQuestion6, dict(iq_answer_6="R6")
            yield IQQuestion7, dict(iq_answer_7="R7")
            yield IQQuestion8, dict(iq_answer_8="R3")
            yield IQQuestion9, dict(iq_answer_9="R2")
            yield IQQuestion10, dict(iq_answer_10="R5")
            yield IQEnd
            yield Part2Intro
            yield IQTransition
            yield GameSummaryInstructions

        yield RoundStart
        assert self.player.participant_iq_score == 10
        assert self.player.iq_rank in C.NUMBER_CHOICES
        assert self.player.sender_id
        assert self.player.sender_number == self.player.iq_rank
        assert self.player.previous_participant_1_id
        assert self.player.previous_participant_2_id
        if self.round_number == C.NUM_ROUNDS:
            ranks = {round_player.iq_rank for round_player in self.player.in_all_rounds()}
            assert len(ranks) > 1
        available_numbers = sender_message_numbers(self.player.sender_message)
        assert self.player.sender_number in available_numbers
        chosen_guess = available_numbers[-1]
        yield ReceiverDecision, dict(guess=chosen_guess)
        assert self.player.guess == chosen_guess

        if self.round_number == C.NUM_ROUNDS:
            export_rows = list(custom_export(self.player.in_all_rounds()))
            assert export_rows[0][0:4] == [
                "participant_id_in_session",
                "participant_code",
                "round_1_participant_iq_score",
                "round_1_participant_iq_performance",
            ]
            assert "round_10_guess" in export_rows[0]
            assert "education_level" in export_rows[0]
            data_rows = export_rows[1:]
            participant_codes = {row[1] for row in data_rows}
            assert len(data_rows) == len(participant_codes)
            assert self.player.participant.code in participant_codes
            yield DemographicsIntro
            yield DemographicsQuestionnaire, dict(
                age=25,
                gender="Female",
                education_level="Bachelors Degree",
            )
            yield Submission(StudyComplete, check_html=False)
