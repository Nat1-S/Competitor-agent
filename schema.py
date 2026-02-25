"""
Pydantic schema for the Senior Product Manager Agent analysis.

All field values should be populated in Hebrew for display in the UI.
The schema enforces structure and validation for the LLM output.
"""

from typing import Optional
from pydantic import BaseModel, Field


# --- Single Product Analysis Components ---

class ProductEssence(BaseModel):
    """What the product does and what problem it solves."""
    description: str = Field(
        description="תיאור מה המוצר עושה בפועל"
    )
    problem_solved: str = Field(
        description="איזו בעיה המוצר פותר"
    )


class Strategy(BaseModel):
    """Target audience, positioning, and business model."""
    target_audience: str = Field(
        description="קהל היעד"
    )
    positioning: str = Field(
        description="מיצוב המוצר בשוק"
    )
    business_model: str = Field(
        description="מודל עסקי"
    )


class StrengthsWeaknesses(BaseModel):
    """Critical analysis of UX, value proposition, and gaps."""
    strengths: list[str] = Field(
        description="נקודות חוזק",
        default_factory=list
    )
    weaknesses: list[str] = Field(
        description="נקודות חולשה",
        default_factory=list
    )


class QAOptimization(BaseModel):
    """Friction points and suggestions for improvement."""
    friction_points: list[str] = Field(
        description="נקודות חיכוך פוטנציאליות",
        default_factory=list
    )
    suggestions: list[str] = Field(
        description="הצעות לשיפור ויעילות",
        default_factory=list
    )


class SingleProductAnalysis(BaseModel):
    """Full analysis of one product."""
    product_name: str = Field(description="שם המוצר")
    product_url: str = Field(description="כתובת URL של המוצר")
    essence: ProductEssence
    strategy: Strategy
    feature_inventory: list[str] = Field(
        description="מפת יכולות מרכזיות",
        default_factory=list
    )
    strengths_weaknesses: StrengthsWeaknesses
    qa_optimization: QAOptimization


# --- Comparison (Multi-Product) Output ---

class ComparisonRow(BaseModel):
    """One row in the side-by-side comparison table."""
    dimension: str = Field(description="מימד להשוואה (למשל: קהל יעד, מודל עסקי)")
    values: list[str] = Field(
        description="ערכים לכל מוצר בסדר ה-URLים שהוזנו",
        default_factory=list
    )


class StrategicProductReport(BaseModel):
    """
    Full output schema for the PM Agent.
    Supports both single product and multi-product comparison.
    """
    # Individual product analyses (one per URL)
    product_analyses: list[SingleProductAnalysis] = Field(
        description="ניתוח מפורט לכל מוצר",
        default_factory=list
    )
    # Side-by-side comparison (only when multiple products)
    comparison_table: list[ComparisonRow] = Field(
        description="טבלת השוואה צד-בצד בין המוצרים",
        default_factory=list
    )
    # Executive summary in Hebrew
    executive_summary: str = Field(
        description="סיכום מנהלים של הניתוח",
        default=""
    )
