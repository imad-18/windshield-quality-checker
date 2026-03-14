from sqlalchemy import Column, Integer, Float, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class WindshieldTest(Base):
    """Stores one test record per windshield."""
    __tablename__ = "windshield_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tension = Column(Float, nullable=False)
    final_intensity = Column(Float, nullable=False)
    final_resistance = Column(Float, nullable=False)
    result = Column(String(10), nullable=False)   # "OK" or "ERROR"
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "tension": self.tension,
            "final_intensity": self.final_intensity,
            "final_resistance": self.final_resistance,
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
