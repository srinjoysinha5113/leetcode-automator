from typing import List, Optional
from app.database import DatabaseManager, get_db
from app.models import ProblemDB, ProblemStatus

class ProblemQueue:
    """Manages ordered, safe retrieval of problems for processing and recovery."""

    @staticmethod
    def get_queued_problems(
        limit: Optional[int] = None,
        slug: Optional[str] = None,
        include_rejected: bool = False
    ) -> List[ProblemDB]:
        """
        Retrieves problems ready for execution.
        Skips already ACCEPTED problems to prevent duplicate submissions.
        """
        with get_db() as db:
            if slug:
                problem = db.query(ProblemDB).filter_by(slug=slug).first()
                return [problem] if problem else []

            query = db.query(ProblemDB).order_by(ProblemDB.order_index.asc())

            # Filter out ACCEPTED problems
            query = query.filter(ProblemDB.status != ProblemStatus.ACCEPTED.value)

            if not include_rejected:
                # Exclude REJECTED or SKIPPED unless explicitly requested
                query = query.filter(ProblemDB.status != ProblemStatus.REJECTED.value)
                query = query.filter(ProblemDB.status != ProblemStatus.SKIPPED.value)

            if limit and limit > 0:
                query = query.limit(limit)

            return query.all()

    @staticmethod
    def get_problem_by_slug(slug: str) -> Optional[ProblemDB]:
        return DatabaseManager.get_problem(slug)

    @staticmethod
    def reset_for_retry(slug: str) -> bool:
        return DatabaseManager.reset_problem(slug)
