import datetime
from intellect.Intellect import Intellect
from application.workspace.models import (
    WorkspaceUser,
    WorkspaceDate,
    WorkspaceRule,
    WorkspaceRuleTypes
)
from application.balances.models import DayOff


class LeaveDay:

    def __init__(self, date, is_official_holiday, leave):
        self._date = date
        self._is_official_holiday = is_official_holiday
        self._leave = leave

    @property
    def date(self):
        return self._date

    @property
    def leave(self):
        return self._leave

    @property
    def is_official_holiday(self):
        return self._is_official_holiday


class BalanceCalculationRulePayload:

    def __init__(self, start_date):
        self._start_date = start_date

        self._left_paid_leaves = 0
        self._left_unpaid_leaves = 0
        self._left_sick_leaves = 0
        self._total_paid_leaves = 0
        self._total_unpaid_leaves = 0
        self._total_sick_leaves = 0

    @property
    def start_date(self):
        return self._start_date

    @property
    def left_paid_leaves(self):
        return self._left_paid_leaves

    @left_paid_leaves.setter
    def left_paid_leaves(self, val):
        self._left_paid_leaves = val

    @property
    def left_unpaid_leaves(self):
        return self._left_unpaid_leaves

    @left_unpaid_leaves.setter
    def left_unpaid_leaves(self, val):
        self._left_unpaid_leaves = val

    @property
    def left_sick_leaves(self):
        return self._left_sick_leaves

    @left_sick_leaves.setter
    def left_sick_leaves(self, val):
        self._left_sick_leaves = val

    @property
    def total_paid_leaves(self):
        return self._total_paid_leaves

    @total_paid_leaves.setter
    def total_paid_leaves(self, val):
        self._total_paid_leaves = val

    @property
    def total_unpaid_leaves(self):
        return self._total_unpaid_leaves

    @total_unpaid_leaves.setter
    def total_unpaid_leaves(self, val):
        self._total_unpaid_leaves = val

    @property
    def total_sick_leaves(self):
        return self._total_sick_leaves

    @total_sick_leaves.setter
    def total_sick_leaves(self, val):
        self._total_sick_leaves = val


class DayOffValidationPayload:

    def __init__(self, leave, user_start_date, balance):
        self._leave = leave
        self._user_start_date = user_start_date
        self._balance = balance

        self._errors = []
        self._warnings = []
        self._notes = []
        self._is_rejected = False

    @property
    def leave(self):
        return self._leave

    @property
    def user_start_date(self):
        return self._user_start_date

    @property
    def balance(self):
        return self._balance

    @property
    def errors(self):
        return self._errors

    @property
    def warnings(self):
        return self._warnings

    @property
    def notes(self):
        return self._notes

    @property
    def is_rejected(self):
        return self._is_rejected

    @is_rejected.setter
    def is_rejected(self, val):
        self._is_rejected = val


def _leaves_to_leave_days(leaves):
    for leave in leaves:

        holidays = WorkspaceDate.query(). \
            filter(WorkspaceDate.date.between(leave.start_date, leave.end_date)). \
            filter(WorkspaceDate.ws_id == leave.workspace_id). \
            filter(WorkspaceDate.is_official_holiday is True). \
            all()

        holiday_dates = map(lambda h: h.date, holidays)

        date = leave.start_date

        while date <= leave.end_date:
            yield LeaveDay( date=date, leave=leave, is_official_holiday=date in holiday_dates)
            date = date + datetime.timedelta(days=1)


# TODO: consider moving execution methods to classes
def execute_balance_calculation_rule(ws_id, user_id):
    ws_rule = WorkspaceRule.find(ws_id=ws_id, type=WorkspaceRuleTypes.BALANCE_CALCULATION)

    if not ws_rule:
        raise Exception('Balance Calculation rule has\'t been defined for workspace.')

    leaves = DayOff.query(). \
        filter(DayOff.user_id == user_id). \
        filter(DayOff.workspace_id == ws_id). \
        all()

    ws_user = WorkspaceUser.find(user_id=user_id, ws_id=ws_id)

    rule_payload = BalanceCalculationRulePayload(start_date=ws_user.start_date)

    intellect = Intellect()
    intellect.learn_policy(ws_rule.rule)

    for leave_day in _leaves_to_leave_days(leaves):
        intellect.learn_fact(leave_day)

    intellect.learn_fact(rule_payload)
    intellect.reason()

    return rule_payload


def execute_day_off_validation_rule(day_off):

    balance = execute_balance_calculation_rule(ws_id=day_off.workspace_id, user_id=day_off.user_id)

    ws_rule = WorkspaceRule.find(ws_id=day_off.workspace_id, type=WorkspaceRuleTypes.DAY_OFF_VALIDATION)

    if not ws_rule:
        raise Exception('Day Off Validation rule has\'t been defined for workspace.')

    # leaves = DayOff.query(). \
    #     filter(DayOff.user_id == day_off.user_id). \
    #     filter(DayOff.workspace_id == day_off.workspace_id). \
    #     all()

    ws_user = WorkspaceUser.find(user_id=day_off.user_id, ws_id=day_off.workspace_id)

    rule_payload = DayOffValidationPayload(
        user_start_date=ws_user.start_date,
        leave=day_off,
        balance=balance
    )

    intellect = Intellect()
    intellect.learn_policy(ws_rule.rule)

    for leave_day in _leaves_to_leave_days([day]):
        intellect.learn_fact(leave_day)

    intellect.learn_fact(rule_payload)
    intellect.reason()

    return rule_payload



