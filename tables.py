from flask_table import Table, Col, OptCol


class IngredientTraceabilityTable(Table):
    name = Col('Name')
    batch = Col('Batch')


class AssemblyTable(Table):
    product_name = Col('name')
    start_time = Col('start time')
    finish_time = Col('Assembly finish time')


class TraceTable(Table):
    name = Col('name')
    batch = Col('batch')
