from pydantic import BaseModel, Field


class MelaRecipe(BaseModel):
    title: str = Field(description="The title of the recipe")
    text: str = Field(
        default="",
        description="Short description of the recipe displayed after the title",
    )
    yield_: str = Field(
        alias="yield",
        description="Yield or number of servings (e.g., '4 servings', '12 cookies')",
    )
    prepTime: str = Field(description="Preparation time (e.g., '15 minutes', '1 hour')")
    cookTime: str = Field(description="Cooking time (e.g., '30 minutes', '2 hours')")
    totalTime: str = Field(description="Total time to prepare and cook the dish")
    ingredients: str = Field(
        description="Ingredients list, with each ingredient on a new line separated by \\n. Use # for group titles like '# For the sauce'"
    )
    instructions: str = Field(
        description="Step-by-step cooking instructions, with each step on a new line separated by \\n. "
    )
    notes: str = Field(
        default="", description="Additional notes, tips, or variations for the recipe"
    )
    images: list[str] = Field(
        default_factory=list,
        description="Always leave this as an empty list []",
    )
    categories: list[str] = Field(
        default_factory=list, description="Array of category names"
    )
    nutrition: str = Field(default="", description="Nutrition information")
    link: str = Field(default="", description="Source of the recipe")
