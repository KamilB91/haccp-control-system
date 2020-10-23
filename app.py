from flask import Flask, url_for, render_template, g, flash, redirect, request
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
import models
import forms
from config import INGREDIENT_CATEGORY

app = Flask(__name__)
app.secret_key = 'nHJBKJhkj3uhun3enml,;LK@JiwnNme,,e2moke2e,l1moiouUu2m3oiIIOII(&&uh42*@'

models.initialize()
models.test()

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


@app.route('/production_day/<process_type>')
def production_day(process_type):
    models.ProductionDay.create(
        date=datetime.date.today().strftime('%x'),
        batch=datetime.date.today().strftime('%y%j')
    )
    return redirect(url_for('process', process_type=process_type))


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
    production_day = models.ProductionDay.get_or_none(date=datetime.date.today())
    forms.PickProduct.product = forms.SelectField('Product', choices=[x.name for x in models.Product.select()])
    form = forms.PickProduct()
    cooked_products = models.CookedProduct.select()
    if form.validate_on_submit():
        models.CookedProduct.create(
            name=form.product.data,
            date=datetime.date.today()
        )
        product = models.CookedProduct.get(name=form.product.data)
        if process_type == 'assembly-cooking':
            models.Process.create(
                product=product
            )
        else:
            models.Process.create(
                process_type=process_type,
                product=product
            )

        product = models.Product.get(name=form.product.data)
        ingredients = product.get_ingredients()
        for i in ingredients:
            print(i.product.name, i.ingredient.name)

    return render_template('process.html', form=form, cooked_products=cooked_products,
                           process_type=process_type, production_day=production_day)


@app.route('/update_process/<process_id>', methods=['POST', 'GET'])
def update_process(process_id):
    process_to_update = models.Process.get(id=process_id)
    product = models.CookedProduct.get(id=process_to_update.product.id)
    if request.method == 'POST':
        process_to_update.start_time = request.form['start']
        process_to_update.finish_time = request.form['finish']
        process_to_update.temperature = request.form['temp']

        if process_to_update.process_type == 'cooking':
            models.Process.create(
                product=product
            )
        elif process_to_update.process_type == 'assembly-cooking':
            models.Process.create(
                process_type='cooling',
                product=product
            )

        try:
            if request.form['process']:
                process_to_update.process_type = request.form['process']
                if request.form['process'] == 'assembly-assembly':
                    models.Process.create(
                        process_type='assembly-cooking',
                        product=product
                    )
                elif request.form['process'] == 'cooling-cooling':
                    models.Process.create(
                        process_type='cooling',
                        product=product
                    )

        except KeyError:
            pass

        process_to_update.save()

    return redirect(url_for('process', process_type=process_to_update.process_type))


@app.route('/low-risk')
def low_risk():
    pass


if __name__ == '__main__':
    app.run(threaded=True)
