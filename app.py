from flask import Flask, url_for, render_template, g, flash, redirect, request
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
import models
import forms
from config import INGREDIENT_CATEGORY

app = Flask(__name__)
app.secret_key = 'nHJBKJhkj3uhun3enml,;LK@JiwnNme,,e2moke2e,l1moiouUu2m3oiIIOII(&&uh42*@'

models.initialize()


# login_manager = LoginManager()
# login_manager.init_app(app)


# @login_manager.user_loader
# def load_user(userid):
    #try:
        #return models.User.get(models.User.id == userid)
    #except models.DoesNotExist:
        #return None


@app.before_request
def before_request():
    g.db = models.DB
    g.db.connect()
    # g.user = current_user


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route('/')
def index():
    return render_template('layout.html')


@app.route('/add_ingredient', methods=('GET', 'POST'))
def add_ingredient():
    form = forms.AddIngredientForm()
    if form.validate_on_submit():
        flash("Ingredient added")
        models.Ingredient.create_ingredient(
            name=form.name.data,
            category=form.category.data
        )
        return redirect(url_for('add_ingredient'))
    return render_template('add_ingredient.html', form=form)


@app.route('/add_product', methods=('GET', 'POST'))
def add_product():
    forms.IngredientCheckboxForm.ingredient_checkbox = forms.MultiCheckboxField(
            'Ingredients', choices=[(item.name, item.name) for item in models.Ingredient.select()]
        )
    form = forms.AddProductForm()
    if form.validate_on_submit():
        flash("Product added")
        models.Product.create_product(name=form.name.data)
        for checkbox_data in form.ingredients_checkbox.data['ingredient_checkbox']:
            models.ProductIngredient.create(
                product=models.Product.get(name=form.name.data),
                ingredient=models.Ingredient.get(name=checkbox_data)
            )
        return redirect(url_for('product_list'))
    return render_template('add_product.html', form=form)


@app.route('/product_list')
@app.route('/product_list/<product>')
def product_list(product=None):
    if product:
        product = models.Product.get(name=product)
        ingredients = (x.ingredient for x in product.get_ingredients())
        return render_template('product.html', product=product, ingredients=ingredients)
    else:
        products = models.Product.select()
        return render_template('products_list.html', products=products)


@app.route('/ingredient/<ingredient_id>', methods=['GET', 'POST'])
def ingredient(ingredient_id):
    form = forms.AddBatchCode()
    ingredient = models.Ingredient.get(id=ingredient_id)
    if form.validate_on_submit():
        models.BatchCode.create(
            batch_code=form.batch_code.data,
            ingredient=ingredient
        )
    return render_template('ingredient.html', form=form, ingredient=ingredient)


@app.route('/ingredients_list')
def ingredients_list():
    ingredients = models.Ingredient.select()
    return render_template('ingredients_list.html', ingredients=ingredients, categories=INGREDIENT_CATEGORY)


@app.route('/deactivate_batch_code/<batch_code_id>/<ingredient_id>')
def deactivate_batch_code(batch_code_id, ingredient_id):
    batch_code = models.BatchCode.get(id=batch_code_id)
    batch_code.active = False
    batch_code.save()
    return redirect(url_for('ingredient', ingredient_id=ingredient_id))


@app.route('/process/<process_type>', methods=['POST', 'GET'])
def process(process_type):
    forms.PickProduct.product = forms.SelectField('Product', choices=[x.name for x in models.Product.select()])
    form = forms.PickProduct()
    cooked_products = models.CookedProduct.select()
    if form.validate_on_submit():
        models.CookedProduct.create(
            name=form.product.data,
            date=datetime.datetime.now()
        )
        product = models.CookedProduct.get(name=form.product.data)
        models.Process.create(
            process_type=process_type,
            product=product
        )
    return render_template('process.html', form=form, cooked_products=cooked_products, process_type=process_type)


@app.route('/update_process/<process_type>/<process_id>', methods=['POST', 'GET'])
def update_process(process_type, process_id):
    if request.method == 'POST':
        process = models.Process.get(id=process_id)
        process.start_time = request.form['start']
        process.finish_time = request.form['finish']
        process.temperature = request.form['temp']
        process.save()
    return redirect(url_for('process', process_type=process_type))


if __name__ == '__main__':
    app.run(threaded=True)
