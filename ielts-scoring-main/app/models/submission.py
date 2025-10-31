# File: app/models/submission.py
from sqlalchemy import Column, String, Float, Enum, Text
from ..database import Base
import enum


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    audio_path = Column(String)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)

    topic_prompt = Column(Text, nullable=True)

    transcript = Column(Text, nullable=True)
    fluency = Column(Float, nullable=True)
    pronunciation = Column(Float, nullable=True)
    grammar = Column(Float, nullable=True)
    vocabulary = Column(Float, nullable=True)

    task_response = Column(Float, nullable=True)

    grammar_feedback = Column(Text, nullable=True)
    vocabulary_feedback = Column(Text, nullable=True)
    task_response_feedback = Column(Text, nullable=True)
    overall_feedback = Column(Text, nullable=True)

    # Chúng ta đã bỏ qua trường 'overall' vì nó có thể được tính toán động
    # Nhưng nếu muốn lưu lại, hãy thêm dòng này:
    overall = Column(Float, nullable=True)