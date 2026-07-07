from app.core.database import Base

class LMSNote(Base):
    __tablename__ = "lms_notes"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
