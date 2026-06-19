from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base

class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Версия документа — например "1.0", "1.1"
    # Когда мы обновим оферту, старые записи останутся со старой версией
    document_version = Column(String, nullable=False)
    
    # Тип документа: "oferta", "privacy_policy", "terms"
    document_type = Column(String, nullable=False)
    
    # Дата и время принятия — автоматически
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())