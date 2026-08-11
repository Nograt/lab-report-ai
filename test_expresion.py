from app.schemas.calculation import CalculationSpecification


calculation = CalculationSpecification.model_validate(
    {
        "output": "PK",
        "unit": "W",
        "expression": {
            "type": "operation",
            "operation": "subtract",
            "args": [
                {
                    "type": "variable",
                    "name": "P"
                },
                {
                    "type": "variable",
                    "name": "Pap"
                }
            ]
        }
    }
)


print(
    calculation.model_dump_json(
        indent=2
    )
)