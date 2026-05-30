class TicketValidationError(Exception):
    """Levée lorsqu'une règle métier sur le contenu d'un ticket est violée."""


class UserValidationError(Exception):
    """Levée lorsqu'une règle métier sur la création ou modification d'un utilisateur est violée."""
