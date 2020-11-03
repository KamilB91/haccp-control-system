from flask_table import Table, Col, OptCol


class IngredientTraceabilityTable(Table):
    name = Col('Name')
    batch = Col('Batch')


class AssemblyTable(Table):
    product_name = Col('name')
    assembly_start_time = Col('start time')
    assembly_finish_time = Col('Assembly finish time')