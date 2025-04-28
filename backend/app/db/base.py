# Import all the models, so that Base knows about them before being
# imported by Alembic
from backend.app.db.base_class import Base  # Import the base class
from backend.app.models.user import User  # Import your models here
from backend.app.models.session import ConversationSession # Import Session model

# Potentially import other models as they are created
# from backend.app.models.other import OtherModel

__all__ = ["Base", "User", "ConversationSession"] # Add other models to __all__ as needed 