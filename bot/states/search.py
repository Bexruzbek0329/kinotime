"""FSM state group for search flow."""
from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    """States used during the interactive search flow."""

    waiting_for_query = State()
