from flask_wtf import FlaskForm, Form
from wtforms import StringField, widgets, SelectMultipleField, FormField, SelectField, TimeField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Length
from config import INGREDIENT_CATEGORY

from models import Product, Ingredient


def product_exists(form, field):
    if Product.select().where(Product.name == field.data).exists():
        raise ValidationError('This product already exists in database.')


def ingredient_exists(form, field):
    if Ingredient.select().where(Ingredient.name == field.data).exists():
        raise ValidationError('This ingredient already exists in database.')


class AddIngredientForm(FlaskForm):
    name = StringField(
        'Ingredient name',
        validators=[
            DataRequired(),
            Length(min=3),
            ingredient_exists
        ]
    )
    category = SelectField('Ingredient category', choices=[x for x in INGREDIENT_CATEGORY])


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class IngredientCheckboxForm(Form):
    ingredient_checkbox = MultiCheckboxField()


class AddProductForm(FlaskForm):
    name = StringField(
        'Product name',
        validators=[
            DataRequired(),
            Length(min=3),
            product_exists
        ]
    )
    ingredients_checkbox = FormField(IngredientCheckboxForm)


class AddBatchCode(FlaskForm):
    batch_code = StringField(
        'New Batch code',
        validators=[
            DataRequired(),
            Length(min=3)
        ]
    )


class PickProduct(FlaskForm):
    product = SelectField()


class ProcessDetails(FlaskForm):
    start_time = TimeField(
        'start time',
        validators=[
            DataRequired()
        ]
    )
    finish_time = TimeField(
        'finish time',
        validators=[
            DataRequired()
        ]
    )
    temperature = IntegerField(
        'temp.',
        validators=[
            DataRequired()
        ]
    )
