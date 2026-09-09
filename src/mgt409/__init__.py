"""MGT 409 homework package.

Small, reusable helpers for the course assignments. Keeping shared logic here
lets each assignment script and notebook import tested code instead of copying
snippets around.
"""

from .stats import describe, moving_average, summary_table

__all__ = ["describe", "moving_average", "summary_table"]
