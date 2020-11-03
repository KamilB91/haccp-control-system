import datetime

from peewee import *

DB = SqliteDatabase('database.db')


class BaseModel(Model):
    class Meta:
        database = DB


class User(BaseModel):
    username = CharField()
    password = CharField()


# models to create relations and control batch codes
class Product(BaseModel):
    name = CharField(unique=True)

    def get_ingredients(self):
        return (
            ProductIngredient.select().where(ProductIngredient.product == self)
        )

    @classmethod
    def create_product(cls, name):
        try:
            with DB.transaction():
                cls.create(
                    name=name
                )
        except IntegrityError:
            raise ValueError('Product already exists')


class Ingredient(BaseModel):
    name = CharField(unique=True)
    category = CharField()

    def get_batch_codes(self):
        return BatchCode.select().where(BatchCode.ingredient == self)

    @classmethod
    def create_ingredient(cls, name, category):
        try:
            with DB.transaction():
                cls.create(
                    name=name,
                    category=category
                )
        except IntegrityError:
            raise ValueError('Product already exists')


class BatchCode(BaseModel):
    batch_code = CharField()
    ingredient = ForeignKeyField(Ingredient, backref='batch_codes')
    added_at = DateTimeField(default=datetime.datetime.now)
    active = BooleanField(default=True)

    class Meta:
        order_by = ('-added_at',)


class ProductIngredient(BaseModel):
    product = ForeignKeyField(Product, backref='products')
    ingredient = ForeignKeyField(Ingredient, backref='ingredients')


# models to control production processes
class CookedProduct(BaseModel):
    name = CharField()
    date = DateField()

    def get_processes(self):
        return Process.select().where(Process.product == self)  # to delete


class Process(BaseModel):
    process_type = CharField(null=True)
    start_time = TimeField(null=True)
    finish_time = TimeField(null=True)
    temperature = IntegerField(null=True)
    product = ForeignKeyField(CookedProduct, backref='processes')


class UsedIngredient(BaseModel):
    name = CharField()
    batch = CharField()
    type = CharField()
    date = DateField()

    @classmethod
    def create_used_ingredient(cls, name, batch, type, date):
        if not UsedIngredient.get_or_none(name=name, batch=batch, date=date):
            with DB.transaction():
                cls.create(
                    name=name,
                    batch=batch,
                    type=type,
                    date=date,
                )


class ProductionDay(BaseModel):
    date = DateField()
    batch = CharField()

    def cooked_products(self):
        return CookedProduct.select().where(CookedProduct.date == self.date)

    def used_ingredients(self):
        return UsedIngredient.select().where(UsedIngredient.date == self.date)


def initialize():
    if not DB.is_closed():
        DB.close()

    DB.connect()
    DB.create_tables([User, Product, Ingredient, BatchCode, ProductIngredient,
                      CookedProduct, Process, UsedIngredient, ProductionDay], safe=True)
    DB.close()


def test():
    """
    product = Product.get(name='Lasagne')
    ingredients = product.get_ingredients()
    for i in ingredients:
        print(i.product.name, i.ingredient.name)
    """
    """
    DB.connect()
    processes = Process.select()
    for process in processes:
        print(process.id, process.process_type, process.start_time, process.finish_time, process.temperature,
              process.product.id, process.product.name)
    """
