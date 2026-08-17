from docx.oxml import OxmlElement
from docx.oxml.ns import qn


SUBSCRIPT_CHARACTERS = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "ₐ": "a",
    "ₑ": "e",
    "ₕ": "h",
    "ᵢ": "i",
    "ⱼ": "j",
    "ₖ": "k",
    "ₗ": "l",
    "ₘ": "m",
    "ₙ": "n",
    "ₒ": "o",
    "ₚ": "p",
    "ᵣ": "r",
    "ₛ": "s",
    "ₜ": "t",
    "ᵤ": "u",
    "ᵥ": "v",
    "ₓ": "x",
}


def format_equation_number(
    value: float | int,
) -> str:
    value = float(value)

    if value == 0:
        return "0"

    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))

    formatted = f"{value:.6f}"

    return (
        formatted
        .rstrip("0")
        .rstrip(".")
    )


def format_result_number(
    value: float | int,
) -> str:
    value = float(value)

    if value == 0:
        return "0"

    absolute = abs(value)

    if absolute < 0.01:
        formatted = f"{value:.6f}"

    elif absolute < 1:
        formatted = f"{value:.4f}"

    elif absolute < 100:
        formatted = f"{value:.3f}"

    else:
        formatted = f"{value:.2f}"

    return (
        formatted
        .rstrip("0")
        .rstrip(".")
    )


def _math_run(
    text: str,
    plain: bool = False,
):
    run = OxmlElement("m:r")

    if plain:
        run_properties = OxmlElement(
            "m:rPr"
        )

        style = OxmlElement(
            "m:sty"
        )

        style.set(
            qn("m:val"),
            "p",
        )

        run_properties.append(
            style
        )

        run.append(
            run_properties
        )

    text_element = OxmlElement(
        "m:t"
    )

    text_element.text = str(text)

    run.append(
        text_element
    )

    return run


def _split_subscript(
    variable: str,
) -> tuple[str, str | None]:
    position = len(variable)

    while (
        position > 0
        and variable[position - 1]
        in SUBSCRIPT_CHARACTERS
    ):
        position -= 1

    if position == len(variable):
        return variable, None

    base = variable[:position]

    subscript = "".join(
        SUBSCRIPT_CHARACTERS[character]
        for character in variable[position:]
    )

    return base, subscript


def _append_variable(
    parent,
    variable: str,
):
    base, subscript = _split_subscript(
        variable
    )

    if subscript is None:
        parent.append(
            _math_run(base)
        )
        return

    sub = OxmlElement(
        "m:sSub"
    )

    element = OxmlElement(
        "m:e"
    )

    element.append(
        _math_run(base)
    )

    sub_element = OxmlElement(
        "m:sub"
    )

    sub_element.append(
        _math_run(subscript)
    )

    sub.append(element)
    sub.append(sub_element)

    parent.append(sub)


def _expression_precedence(
    expression: dict,
) -> int:
    if expression["type"] != "operation":
        return 10

    operation = expression["operation"]

    if operation in {
        "add",
        "subtract",
    }:
        return 1

    if operation in {
        "multiply",
        "divide",
    }:
        return 2

    if operation == "power":
        return 3

    return 4


def _create_delimiter(
    expression: dict,
    variables: dict[str, float] | None,
    substitute: bool,
):
    delimiter = OxmlElement(
        "m:d"
    )

    properties = OxmlElement(
        "m:dPr"
    )

    begin = OxmlElement(
        "m:begChr"
    )

    begin.set(
        qn("m:val"),
        "(",
    )

    end = OxmlElement(
        "m:endChr"
    )

    end.set(
        qn("m:val"),
        ")",
    )

    properties.append(begin)
    properties.append(end)

    delimiter.append(properties)

    element = OxmlElement(
        "m:e"
    )

    _append_expression_core(
        parent=element,
        expression=expression,
        variables=variables,
        substitute=substitute,
    )

    delimiter.append(element)

    return delimiter


def _append_expression(
    parent,
    expression: dict,
    variables: dict[str, float] | None = None,
    substitute: bool = False,
    parent_precedence: int = 0,
):
    precedence = _expression_precedence(
        expression
    )

    if precedence < parent_precedence:
        parent.append(
            _create_delimiter(
                expression=expression,
                variables=variables,
                substitute=substitute,
            )
        )

        return

    _append_expression_core(
        parent=parent,
        expression=expression,
        variables=variables,
        substitute=substitute,
    )


def _append_expression_core(
    parent,
    expression: dict,
    variables: dict[str, float] | None,
    substitute: bool,
):
    expression_type = expression[
        "type"
    ]


    if expression_type == "variable":
        name = expression["name"]

        if substitute:
            if variables is None:
                raise ValueError(
                    "Variables are required "
                    "for substitution."
                )

            if name not in variables:
                raise ValueError(
                    f"Missing substitution "
                    f"value for '{name}'."
                )

            parent.append(
                _math_run(
                    format_equation_number(
                        variables[name]
                    )
                )
            )

        else:
            _append_variable(
                parent=parent,
                variable=name,
            )

        return

    if expression_type == "constant":
        parent.append(
            _math_run(
                format_equation_number(
                    expression["value"]
                )
            )
        )

        return


    if expression_type != "operation":
        raise ValueError(
            "Unsupported expression type."
        )

    operation = expression[
        "operation"
    ]

    args = expression[
        "args"
    ]



    if operation == "add":
        for index, arg in enumerate(args):
            if index > 0:
                parent.append(
                    _math_run(
                        " + ",
                        plain=True,
                    )
                )

            _append_expression(
                parent=parent,
                expression=arg,
                variables=variables,
                substitute=substitute,
                parent_precedence=1,
            )

        return

    if operation == "subtract":
        if len(args) != 2:
            raise ValueError(
                "Subtract requires exactly "
                "two arguments."
            )

        _append_expression(
            parent=parent,
            expression=args[0],
            variables=variables,
            substitute=substitute,
            parent_precedence=1,
        )

        parent.append(
            _math_run(
                " - ",
                plain=True,
            )
        )

        _append_expression(
            parent=parent,
            expression=args[1],
            variables=variables,
            substitute=substitute,
            parent_precedence=2,
        )

        return

    if operation == "multiply":
        for index, arg in enumerate(args):
            if index > 0:
                parent.append(
                    _math_run(
                        " · ",
                        plain=True,
                    )
                )

            _append_expression(
                parent=parent,
                expression=arg,
                variables=variables,
                substitute=substitute,
                parent_precedence=2,
            )

        return

    if operation == "divide":
        if len(args) != 2:
            raise ValueError(
                "Divide requires exactly "
                "two arguments."
            )

        fraction = OxmlElement(
            "m:f"
        )

        numerator = OxmlElement(
            "m:num"
        )

        denominator = OxmlElement(
            "m:den"
        )

        _append_expression(
            parent=numerator,
            expression=args[0],
            variables=variables,
            substitute=substitute,
        )

        _append_expression(
            parent=denominator,
            expression=args[1],
            variables=variables,
            substitute=substitute,
        )

        fraction.append(
            numerator
        )

        fraction.append(
            denominator
        )

        parent.append(
            fraction
        )

        return

    if operation == "power":
        if len(args) != 2:
            raise ValueError(
                "Power requires exactly "
                "two arguments."
            )

        power = OxmlElement(
            "m:sSup"
        )

        base = OxmlElement(
            "m:e"
        )

        exponent = OxmlElement(
            "m:sup"
        )

        _append_expression(
            parent=base,
            expression=args[0],
            variables=variables,
            substitute=substitute,
            parent_precedence=3,
        )

        _append_expression(
            parent=exponent,
            expression=args[1],
            variables=variables,
            substitute=substitute,
        )

        power.append(base)
        power.append(exponent)

        parent.append(power)

        return

    if operation == "sqrt":
        if len(args) != 1:
            raise ValueError(
                "Sqrt requires exactly "
                "one argument."
            )

        radical = OxmlElement(
            "m:rad"
        )

        properties = OxmlElement(
            "m:radPr"
        )

        hide_degree = OxmlElement(
            "m:degHide"
        )

        hide_degree.set(
            qn("m:val"),
            "1",
        )

        properties.append(
            hide_degree
        )

        degree = OxmlElement(
            "m:deg"
        )

        element = OxmlElement(
            "m:e"
        )

        _append_expression(
            parent=element,
            expression=args[0],
            variables=variables,
            substitute=substitute,
        )

        radical.append(properties)
        radical.append(degree)
        radical.append(element)

        parent.append(radical)

        return

    if operation in {
        "sin",
        "cos",
        "tan",
        "log",
        "ln",
    }:
        if len(args) != 1:
            raise ValueError(
                f"{operation} requires "
                "one argument."
            )

        parent.append(
            _math_run(
                operation,
                plain=True,
            )
        )

        parent.append(
            _create_delimiter(
                expression=args[0],
                variables=variables,
                substitute=substitute,
            )
        )

        return

    if operation == "abs":
        if len(args) != 1:
            raise ValueError(
                "Abs requires one argument."
            )

        parent.append(
            _math_run(
                "|",
                plain=True,
            )
        )

        _append_expression(
            parent=parent,
            expression=args[0],
            variables=variables,
            substitute=substitute,
        )

        parent.append(
            _math_run(
                "|",
                plain=True,
            )
        )

        return

    raise ValueError(
        f"Unsupported Word equation "
        f"operation: {operation}"
    )


def append_formula_equation(
    paragraph,
    output: str,
    expression: dict,
):
    equation = OxmlElement(
        "m:oMath"
    )

    _append_variable(
        parent=equation,
        variable=output,
    )

    equation.append(
        _math_run(
            " = ",
            plain=True,
        )
    )

    _append_expression(
        parent=equation,
        expression=expression,
    )

    paragraph._p.append(
        equation
    )


def append_substitution_equation(
    paragraph,
    output: str,
    expression: dict,
    variables: dict[str, float],
):
    equation = OxmlElement(
        "m:oMath"
    )

    _append_variable(
        parent=equation,
        variable=output,
    )

    equation.append(
        _math_run(
            " = ",
            plain=True,
        )
    )

    _append_expression(
        parent=equation,
        expression=expression,
        variables=variables,
        substitute=True,
    )

    paragraph._p.append(
        equation
    )


def append_result_equation(
    paragraph,
    output: str,
    result: float,
    unit: str | None,
):
    equation = OxmlElement(
        "m:oMath"
    )

    _append_variable(
        parent=equation,
        variable=output,
    )

    equation.append(
        _math_run(
            " = ",
            plain=True,
        )
    )

    equation.append(
        _math_run(
            format_result_number(
                result
            )
        )
    )

    if unit:
        equation.append(
            _math_run(
                f" {unit}",
                plain=True,
            )
        )

    paragraph._p.append(
        equation
    )