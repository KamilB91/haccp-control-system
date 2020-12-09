from flask_table import Table, Col, LinkCol, ButtonCol


class IngredientTraceabilityTable(Table):
    name = Col('Name')
    batch = Col('Batch')


class AssemblyTable(Table):
    product_name = Col('Name')
    start_time = Col('Start time')
    finish_time = Col('Assembly finish time')


class TraceTable(Table):
    name = LinkCol('Name', 'ingredient', url_kwargs=dict(ingredient_id='id'), attr='name')
    batch = Col('Batch code')


class ActiveBatchCodeTable(Table):
    batch_code = Col('New')
    spent_button = ButtonCol('Old', 'deactivate_batch_code', url_kwargs=dict(batch_code_id='id', ingredient_id='ingredient_id'))


class DeactiveBatchCodeTable(Table):
    batch_code = Col('Old')
