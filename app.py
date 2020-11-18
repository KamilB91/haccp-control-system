from flask import Flask, url_for, render_template, g, flash, redirect, request
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
import models
import forms
from config import INGREDIENT_CATEGORY
import tables

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
        date=datetime.date.today(),
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
        return render_template('product.html',
                               product=product,
                               ingredients=ingredients)
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
    return render_template('ingredient.html',
                           form=form,
                           ingredient=ingredient)


@app.route('/ingredients_list')
def ingredients_list():
    table = tables.TraceTable
    ingredients = models.Ingredient.select()
    ingredients_tuple = []
    for ingredient in ingredients:
        batch_code = [batch_code.batch_code for batch_code in ingredient.batch_codes if batch_code.active]
        ingredients_tuple.append(dict(name=ingredient.name, batch=batch_code[0]))
    return render_template('ingredients_list.html',
                           table=table(ingredients_tuple),
                           ingredients=ingredients,
                           categories=INGREDIENT_CATEGORY)


@app.route('/deactivate_batch_code/<batch_code_id>/<ingredient_id>')
def deactivate_batch_code(batch_code_id, ingredient_id):
    batch_code = models.BatchCode.get(id=batch_code_id)
    batch_code.active = False
    batch_code.save()
    return redirect(url_for('ingredient', ingredient_id=ingredient_id))


@app.route('/process/<process_type>', methods=['POST', 'GET'])
def process(process_type):
    today = models.ProductionDay.get_or_none(date=datetime.date.today())
    forms.PickProduct.product = forms.SelectField('Product',
                                                  choices=[x.name for x in models.Product.select()])
    form = forms.PickProduct()
    process = None

    if form.validate_on_submit():
        # this form in process.html is not provided for Packing room(process_type=cooling)
        # creates a product to be cooked and its first process
        if process_type == 'assembly-cooking':
            process = models.Process.create(
                product_name=form.product.data,
                date=datetime.date.today()
            )
        elif process_type == 'cooking':
            # if process_type came from the kitchen then process is created with process_type of 'cooking'
            process = models.Process.create(
                product_name=form.product.data,
                process_type=process_type,
                date=datetime.date.today()
            )
        # TODO .join method
        used_ingredients = [x.ingredient for x in models.Product.get(name=process.product_name).get_ingredients()]
        for ingredient in used_ingredients:
            batch_code = [batch for batch in ingredient.get_batch_codes() if batch.active]
            print(batch_code[0].batch_code)
            models.UsedIngredient.create_used_ingredient(
                name=ingredient.name,
                batch=batch_code[0].batch_code,
                type=ingredient.category,
                date=datetime.date.today()
            )

        # if process_type comes from assembly, process creates without process type,
        # that will be chosen later in update_process via select part of form for each product process in processes.html

    processes = models.Process.select().where(models.Process.completed == False)
    for process in processes:
        print(process.product_name, process.process_type, process.completed)

    return render_template('process.html',
                           form=form,
                           processes=processes,
                           process_type=process_type,
                           production_day=today)


@app.route('/update_process/<process_id>', methods=['POST', 'GET'])
def update_process(process_id):
    process_to_update = models.Process.get(id=process_id)
    if request.method == 'POST':
        process_to_update.start_time = request.form['start']
        process_to_update.finish_time = request.form['finish']
        process_to_update.temperature = request.form['temp']
        process_to_update.completed = True

        if process_to_update.process_type == 'cooking':
            models.Process.create(
                product_name=process_to_update.product_name,
                date=datetime.date.today()
            )
        elif process_to_update.process_type == 'assembly-cooking':
            models.Process.create(
                product_name=process_to_update.product_name,
                process_type='cooling',
                date=datetime.date.today()
            )
        return_to = process_to_update.process_type
        try:
            if request.form['process']:
                process_to_update.process_type = request.form['process']
                return_to = 'assembly-cooking'
                if request.form['process'] == 'assembly-assembly':
                    models.Process.create(
                        product_name=process_to_update.product_name,
                        process_type='assembly-cooking',
                        date=datetime.date.today()
                    )
                elif request.form['process'] == 'cooling-cooling':
                    models.Process.create(
                        product_name=process_to_update.product_name,
                        process_type='cooling',
                        date=datetime.date.today()
                    )
        except KeyError:
            pass

        process_to_update.save()

        return redirect(url_for('process', process_type=return_to))


@app.route('/select_day', methods=['GET', 'POST'])
def select_day():
    form = forms.SelectDateForm()
    select_production_day = models.ProductionDay.select()
    if form.validate_on_submit():
        select_production_day = models.ProductionDay.select().where(models.ProductionDay.date == form.date.data)
    return render_template('select_day.html',
                           form=form,
                           select_production_day=select_production_day)


@app.route('/show_day_details/<day_id>')
def show_day_details(day_id):
    selected_day = models.ProductionDay.get(id=day_id)
    cooked_products = models.Process.select().where(models.Process.date == selected_day.date)
    return render_template('show_day_details.html',
                           selected_day=selected_day,
                           cooked_products=cooked_products)


@app.route('/ingredient_traceability/<day_id>')
def ingredient_traceability(day_id):
    table = tables.IngredientTraceabilityTable
    selected_day = models.ProductionDay.get(id=day_id)
    cooked_products = models.Process.select().where(models.Process.date == selected_day.date)
    used_ingredients = models.UsedIngredient.select().where(models.UsedIngredient.date == selected_day.date)
    return render_template('ingredient_traceability.html',
                           selected_day=selected_day,
                           cooked_products=cooked_products,
                           categories=INGREDIENT_CATEGORY,
                           table=table(used_ingredients))


if __name__ == '__main__':
    app.run(threaded=True)
