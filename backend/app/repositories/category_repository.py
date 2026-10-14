from app.models.category import Category
from app.models.enums import CategoryType
from app.repositories.base import BaseRepository

DEFAULT_CATEGORIES = {
    CategoryType.income: ["Salário", "Freelance", "Rendimentos", "Outros"],
    CategoryType.expense: [
        "Alimentação",
        "Moradia",
        "Transporte",
        "Saúde",
        "Educação",
        "Lazer",
        "Compras",
        "Assinaturas",
        "Impostos",
        "Fatura de cartão",
        "Outros",
    ],
}


class CategoryRepository(BaseRepository):
    def get_by_user(self, user_id: str) -> list[Category]:
        return self.list_all(Category, user_id)

    def get_type(self, user_id: str, ctype: CategoryType) -> list[Category]:
        rows = [c for c in self.list_all(Category, user_id) if c.type == ctype]
        rows.sort(key=lambda c: c.name)
        return rows

    def find_by_name(self, user_id: str, name: str, ctype: CategoryType) -> Category | None:
        for cat in self.list_all(Category, user_id):
            if cat.name == name and cat.type == ctype:
                return cat
        return None

    def seed_defaults(self, user_id: str) -> None:
        existing_names = {(c.name, c.type) for c in self.get_by_user(user_id)}
        for ctype, names in DEFAULT_CATEGORIES.items():
            for name in names:
                if (name, ctype) in existing_names:
                    continue
                self.add(
                    Category(
                        user_id=user_id,
                        name=name,
                        type=ctype,
                        is_default=True,
                        active=True,
                    )
                )
        self.commit()