from app.db.session import get_db
from app.models.program import ProgramTemplate
from app.models.user import User
from app.security.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = db.query(ProgramTemplate).filter(ProgramTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    is_owner = template.owner_user_id == current_user.id
    is_creator = template.created_by_user_id == current_user.id

    if not (current_user.is_admin or current_user.is_coach or is_owner or is_creator):
        raise HTTPException(status_code=403, detail="Нет прав на удаление")

    db.delete(template)
    db.commit()
